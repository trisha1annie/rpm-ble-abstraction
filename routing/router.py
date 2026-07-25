from enum import Enum


class RoutingPath(str, Enum):
    STANDARD_GATT = "standard_gatt"
    STANDARD_UNSUPPORTED = "standard_unsupported"
    PROPRIETARY_WOT = "proprietary_wot"
    PROPRIETARY_UNSUPPORTED = "proprietary_unsupported"


class AutomaticRouter:
    def __init__(
        self,
        numbers_database,
        gatt_schema_registry,
        wot_registry,
    ):
        self.numbers_database = numbers_database
        self.gatt_schema_registry = gatt_schema_registry
        self.wot_registry = wot_registry

    def select_path(
        self,
        service_uuid: str,
        characteristic_uuid: str,
    ) -> RoutingPath:
        service_uuid = normalize_uuid(service_uuid)
        characteristic_uuid = normalize_uuid(characteristic_uuid)

        service_is_standard = self.numbers_database.has_service(
            service_uuid
        )
        characteristic_is_standard = (
            self.numbers_database.has_characteristic(
                characteristic_uuid
            )
        )

        decoder_exists = self.gatt_schema_registry.has_schema(
            service_uuid,
            characteristic_uuid,
        )

        if (
            service_is_standard
            and characteristic_is_standard
            and decoder_exists
        ):
            return RoutingPath.STANDARD_GATT

        if service_is_standard and characteristic_is_standard:
            return RoutingPath.STANDARD_UNSUPPORTED

        if self.wot_registry.has_configuration(
            service_uuid,
            characteristic_uuid,
        ):
            return RoutingPath.PROPRIETARY_WOT

        return RoutingPath.PROPRIETARY_UNSUPPORTED