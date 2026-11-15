"""Default driver for BLE route resolution."""
from __future__ import annotations

import inspect
import logging
import asyncio
import time
import csv
from pathlib import Path
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any
import os

from .ble_client import BleClient
from .exceptions import UnexpectedFieldValueError
from .models import DecodedPayload
from .plugin_driver import DriverMeasurement, MeasurementCallback, PluginDriver
from .schema import normalise_uuid
from fault_handling.stream_handler import StreamHandler

_log = logging.getLogger(__name__)

_GENERIC_ATTRIBUTE_SERVICE_UUID = normalise_uuid("1801")
_SERVICE_CHANGED_CHARACTERISTIC_UUID = normalise_uuid("2A05")
_SKIP_SERVICE_UUIDS = frozenset({_GENERIC_ATTRIBUTE_SERVICE_UUID})
_SKIP_CHARACTERISTIC_UUIDS = frozenset({_SERVICE_CHANGED_CHARACTERISTIC_UUID})
_YONKER_OXIMETER_CHAR_UUID = normalise_uuid("cdeacd81-5235-4c07-8846-93a37ee6b86d")


class DriverLifecycleError(RuntimeError):
    pass


def _decode_notification(
    service_uuid: str,
    characteristic_uuid: str,
    payload: bytes,
) -> DecodedPayload:
    from routing.router import router

    return router(service_uuid, characteristic_uuid, payload)


def _supports_route(service_uuid: str, characteristic_uuid: str) -> bool:
    from routing.router import supports_route

    return supports_route(service_uuid, characteristic_uuid)


class StandardPluginDriver:
    def __init__(
        self,
        client: BleClient,
        quality: Mapping[str, Any] | None = None,
    ) -> None:
        self._client = client
        self._quality = dict(quality or {})
        self._on_measurement: MeasurementCallback | None = None
        self._subscriptions: dict[str, str] = {}
        self._started = False
        self._stream_handlers: dict[str, StreamHandler] = {}
        self._dropout_task: asyncio.Task | None = None
        self._fault_csv = None
        self._fault_writer = None
        self._jitter_active: dict[str, bool] = {}

    @property
    def device_id(self) -> str:
        return self._client.device_id

    @property
    def is_started(self) -> bool:
        return self._started

    @property
    def subscribed_characteristics(self) -> frozenset[str]:
        return frozenset(self._subscriptions)

    
    async def start(self, on_measurement: MeasurementCallback) -> None:
        if self._started:
            raise DriverLifecycleError("Driver has already started")

        self._on_measurement = on_measurement

        # Create experimental results directory
        Path("results").mkdir(exist_ok=True)

        experiment = os.getenv("EXPERIMENT", "control")
        run = os.getenv("RUN", "1")

        self._timing_csv = open(
            f"results/oximeter_timing_{experiment}_run{run}.csv",
            "w",
            newline="",
        )

        self._timing_writer = csv.writer(self._timing_csv)

        self._timing_writer.writerow([
            "timestamp",
            "timing_stream_key",
            "interval_ms",
            "baseline_median_ms",
            "baseline_mad_ms",
            "modified_z_score",
            "jitter_ms",
            "anomaly_detected",
            "jitter_detected",
            "raw_jitter_detected",
            "confirmed_jitter_detected"
        ])

        self._fault_csv = open(
            f"results/oximeter_dropout_{experiment}_run{run}.csv",
            "w",
            newline="",
        )

        self._fault_writer = csv.writer(self._fault_csv)

        self._fault_writer.writerow([
            "timestamp",
            "characteristic_uuid",
            "event",
            "observed_interval_ms",
            "baseline_interval_ms",
            "new_rate_hz",
        ])

        self._client.set_disconnected_callback(
            self._handle_unexpected_disconnect
        )

        try:
            await self._client.connect()
            gatt = await self._client.discover_gatt()

            for service in gatt.services:
                service_uuid = normalise_uuid(service.uuid)

                for characteristic in service.characteristics:
                    if not {"notify", "indicate"}.intersection(
                        characteristic.properties
                    ):
                        continue

                    characteristic_uuid = normalise_uuid(
                        characteristic.uuid
                    )

                    if not _supports_route(
                        service_uuid, characteristic_uuid
                    ):
                        continue

                    if characteristic_uuid in self._subscriptions:
                        raise DriverLifecycleError(
                            "A notification characteristic UUID occurs "
                            "in multiple services: "
                            f"{characteristic_uuid}"
                        )

                    # Register timing state before subscribing
                    if characteristic_uuid != _YONKER_OXIMETER_CHAR_UUID:
                        self._stream_handlers[characteristic_uuid] = StreamHandler()

                    self._subscriptions[characteristic_uuid] = service_uuid
                    

                    await self._client.subscribe(
                        characteristic_uuid,
                        self._notification_callback,
                    )

            self._started = True

            if self._subscriptions:
                self._dropout_task = asyncio.create_task(
                    self._monitor_dropouts()
                )

        except Exception:
            await self.stop()
            raise


    async def stop(self) -> None:
        subscriptions = tuple(self._subscriptions)
        self._subscriptions.clear()
        self._started = False
        self._on_measurement = None
        self._client.set_disconnected_callback(None)

        if self._dropout_task is not None:
            self._dropout_task.cancel()

            try:
                await self._dropout_task
            except asyncio.CancelledError:
                pass

            self._dropout_task = None

        self._stream_handlers.clear()
        self._jitter_active.clear()

        for characteristic_uuid in subscriptions:
            await self._client.unsubscribe(characteristic_uuid)
        await self._client.disconnect()
        
        if self._timing_csv is not None:
            self._timing_csv.close()
            self._timing_csv = None
            self._timing_writer = None
        
        if self._fault_csv is not None:
            self._fault_csv.close()
            self._fault_csv = None
            self._fault_writer = None

    def _timing_stream_key(
        self,
        characteristic_uuid: str,
        payload: bytes,
    ) -> str | None:
        if characteristic_uuid == _YONKER_OXIMETER_CHAR_UUID:
            if not payload:
                return None

            if payload[0] == 0x80:
                return f"{characteristic_uuid}:80"

            if payload[0] == 0x81:
                return f"{characteristic_uuid}:81"

            return None

        return characteristic_uuid

    
    async def _notification_callback(
        self,
        characteristic_uuid: str,
        payload: bytes,
    ) -> None:
        arrival_timestamp = time.monotonic()
        normalised_uuid = normalise_uuid(characteristic_uuid)
        service_uuid = self._subscriptions.get(normalised_uuid)
        callback = self._on_measurement
        if service_uuid is None or callback is None:
            return
        
        timing_key = self._timing_stream_key(
            normalised_uuid,
            payload,
        )

        if timing_key is not None:
            if timing_key not in self._stream_handlers:
                self._stream_handlers[timing_key] = StreamHandler()

            self._process_notification_timing(
                timing_key,
                arrival_timestamp,
            )

        try:
            decoded = _decode_notification(service_uuid, normalised_uuid, payload)

            _log.info(
                "DECODED MEASUREMENT [%s]: %s",
                normalised_uuid,
                decoded,
            )

        except UnexpectedFieldValueError as exc:
            _log.debug(
                "Ignoring notification from %s service %s characteristic %s "
                "that does not match its schema: %s",
                self.device_id,
                service_uuid,
                normalised_uuid,
                exc,
            )
            return
        except Exception as exc:
            _log.warning(
                "Unable to decode notification from %s service %s "
                "characteristic %s: %s",
                self.device_id,
                service_uuid,
                normalised_uuid,
                exc,
            )
            return

        result = callback(
            DriverMeasurement(
                device_id=self.device_id,
                service_uuid=service_uuid,
                characteristic_uuid=normalised_uuid,
                payload=decoded,
                received_at=datetime.now(timezone.utc),
                quality=self._quality,
            )
        )
        if inspect.isawaitable(result):
            await result

    async def _handle_unexpected_disconnect(self) -> None:
        task = self._dropout_task
        self._dropout_task = None

        if task is not None:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        self._stream_handlers.clear()
        self._subscriptions.clear()
        self._started = False
        self._on_measurement = None
        self._jitter_active.clear()
    

    def _process_notification_timing(
        self,
        characteristic_uuid: str,
        current_timestamp: float,
    ) -> None:
        handler = self._stream_handlers.get(characteristic_uuid)

        if handler is None:
            return

        
        was_dropout = handler.dropout_active
        previous_timestamp = handler.previous_timestamp

        # Always calculate the observed interval when a previous timestamp exists
        observed_interval = (
            current_timestamp - previous_timestamp
            if previous_timestamp is not None
            else None
        )

        interval = handler.check_notification(current_timestamp)

        # Record recovery on the first notification after a monitored dropout
        if was_dropout:
            _log.info(
                "Notification stream recovered: %s",
                characteristic_uuid,
            )

            self._record_fault_event(
                characteristic_uuid,
                "dropout_recovered",
                observed_interval=observed_interval,
                baseline_interval=(
                    handler.baseline[0]
                    if handler.baseline is not None
                    else None
                ),
            )

        if interval is None and observed_interval is not None:
            if handler.evaluate_long_interval(observed_interval, current_timestamp):
                handler.pending_long_gap = False

                new_rate = 1 / handler.baseline[0]

                _log.warning(
                    "Notification rate changed for %s: %.2f Hz",
                    characteristic_uuid,
                    new_rate,
                )

                self._record_fault_event(
                    characteristic_uuid,
                    "rate_change_detected",
                    observed_interval=observed_interval,
                    baseline_interval=handler.baseline[0],
                    new_rate_hz=new_rate,
                )

                return

        # if handler.last_notification_dropout and not was_dropout:
        #     _log.warning(
        #         "Notification dropout detected from arrival gap: %s",
        #         characteristic_uuid,
        #     )

        #     self._record_fault_event(
        #         characteristic_uuid,
        #         "dropout_detected_from_arrival_gap",
        #         observed_interval=(
        #             current_timestamp - previous_timestamp
        #             if previous_timestamp is not None
        #             else None
        #         ),
        #         baseline_interval=(
        #             handler.baseline[0]
        #             if handler.baseline is not None
        #             else None
        #         ),
        #     )

        if interval is None:
            return

        if handler.baseline is None:
            baseline = handler.establish_baseline(sample_size=50)

            if baseline is not None:
                # Start jitter monitoring with fresh intervals
                handler.reset_jitter_detection()

                _log.info(
                    "Timing baseline established for %s: %.2f ms",
                    characteristic_uuid,
                    baseline[0] * 1000,
                )
            return

        anomaly_detected = False
        rate_changed = handler.detect_rate_change(interval)

        if rate_changed:
            new_rate = 1 / handler.baseline[0]

            _log.warning(
                "Notification rate changed for %s: %.2f Hz",
                characteristic_uuid,
                new_rate,
            )

            self._record_fault_event(
                characteristic_uuid,
                "rate_change_detected",
                observed_interval=interval,
                baseline_interval=handler.baseline[0],
                new_rate_hz=new_rate,
            )
        else:
            anomaly_detected = handler.detect_anomaly(
                interval,
                handler.baseline,
            )

            if anomaly_detected:
                _log.debug(
                    "Individual timing anomaly detected for %s: %.2f ms",
                    characteristic_uuid,
                    interval * 1000,
                )

        jitter = handler.calculate_jitter_window(size=10)

        # Only evaluate jitter when a complete window is available.
        raw_jitter_detected = None
        confirmed_jitter_detected = self._jitter_active.get(
            characteristic_uuid, False
        )

        if jitter is not None:
            raw_jitter_detected = handler.detect_jitter(
                jitter,
                threshold=0.03
            )

            confirmed_jitter_detected = handler.confirm_jitter(
                raw_jitter_detected
            )

            _log.debug(
                "JITTER DEBUG: jitter=%.2f ms, raw=%s, "
                "consecutive=%d, confirmed=%s",
                jitter * 1000,
                raw_jitter_detected,
                handler.consecutive_jitter_warnings,
                confirmed_jitter_detected,
            )

        jitter_detected = confirmed_jitter_detected

        # Record experimental timing data.
        if self._timing_writer is not None:
            median_interval, mad = handler.baseline

            if mad > 0:
                modified_z_score = (
                    0.6745 * (interval - median_interval) / mad
                )
            else:
                modified_z_score = None

            self._timing_writer.writerow([
                current_timestamp,
                characteristic_uuid,
                interval * 1000,
                median_interval * 1000,
                mad * 1000,
                modified_z_score,
                jitter * 1000 if jitter is not None else None,
                anomaly_detected,
                jitter_detected,
                raw_jitter_detected,
                confirmed_jitter_detected,
            ])

            self._timing_csv.flush()

        # Update episode state only when a new jitter window is evaluated.
        if jitter is not None:
            was_active = self._jitter_active.get(
                characteristic_uuid, False
            )

            if jitter_detected and not was_active:
                _log.warning(
                    "Jitter episode detected for %s: %.2f ms",
                    characteristic_uuid,
                    jitter * 1000,
                )

            elif not jitter_detected and was_active:
                _log.info(
                    "Jitter episode ended for %s",
                    characteristic_uuid,
                )

            self._jitter_active[characteristic_uuid] = jitter_detected
    
    async def _monitor_dropouts(self) -> None:
        while True:
            await asyncio.sleep(0.1)

            current_time = time.monotonic()

            for characteristic_uuid, handler in self._stream_handlers.items():
                if handler.baseline is None:
                    continue

                median_interval, mad = handler.baseline
                timeout = 3 * median_interval

                if handler.slowdown_candidate:
                    elapsed = current_time - handler.slowdown_candidate_since

                    # Allow up to 3 seconds to confirm a slower rate
                    if elapsed < 3.0:
                        continue

                    handler.slowdown_candidate = False
                    handler.slowdown_candidate_since = None

                event = handler.monitor_dropout(
                    current_time,
                    timeout,
                )

                if event == "dropout_detected":
                    _log.warning(
                        "Notification dropout detected for %s",
                        characteristic_uuid,
                    )

                    self._record_fault_event(
                        characteristic_uuid,
                        "dropout_detected",
                        baseline_interval=median_interval,
                    )
    
    def _record_fault_event(
        self,
        characteristic_uuid: str,
        event: str,
        observed_interval: float | None = None,
        baseline_interval: float | None = None,
        new_rate_hz: float | None = None,
    ):
        if self._fault_writer is None:
            return

        self._fault_writer.writerow([
            time.monotonic(),
            characteristic_uuid,
            event,
            observed_interval * 1000
            if observed_interval is not None else None,
            baseline_interval * 1000
            if baseline_interval is not None else None,
            new_rate_hz,
        ])

        self._fault_csv.flush()
