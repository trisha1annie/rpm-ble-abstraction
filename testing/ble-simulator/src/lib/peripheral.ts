import bleno from "@stoprocent/bleno";
import { createService } from "./service";
import { registry, clearRegistry } from "./registry";
import type { DeviceConfig } from "../types";

let isAdvertising = false;
let currentConfig: DeviceConfig | null = null;
let eventListenersSet = false;
let pendingCallback: (() => void) | null = null;

export function stopPeripheral(): void {
  if (!isAdvertising) {
    return;
  }

  bleno.stopAdvertising();
  isAdvertising = false;
  clearRegistry();
  pendingCallback = null;
}

export function getCurrentConfig(): DeviceConfig | null {
  return currentConfig;
}

export function startPeripheral(
  config: DeviceConfig,
  callback?: () => void
): void {
  currentConfig = config;
  if (callback) {
    pendingCallback = callback;
  }

  if (!eventListenersSet) {
    bleno.on("stateChange", (state: string) => {
      console.log(`[BLE] State changed: ${state}`);

      if (state === "poweredOn" && currentConfig) {
        if (!isAdvertising) {
          startAdvertisingForConfig(currentConfig);
        }
      } else if (state !== "poweredOn") {
        bleno.stopAdvertising();
        isAdvertising = false;
      }
    });

    bleno.on("advertisingStart", (err?: Error | null) => {
      if (err) {
        console.error("Error in advertisingStart:", err);
        return;
      }

      if (!currentConfig) {
        console.error("No current config when advertising started");
        return;
      }

      const services = currentConfig.services.map((svcConfig) =>
        createService(svcConfig)
      );

      bleno.setServices(services, (err?: Error | null) => {
        if (err) {
          console.error("Error setting services:", err);
          return;
        }

        console.log("[BLE] Services registered");

        console.log("\n📋 Registered characteristics:");
        for (const [name, handle] of Object.entries(registry)) {
          console.log(`   - ${name} (${handle.config.uuid})`);
        }
        console.log("");

        if (pendingCallback) {
          pendingCallback();
          pendingCallback = null;
        }
      });
    });

    bleno.on("accept", (clientAddress: string) => {
      console.log(`[BLE] Client connected: ${clientAddress}`);
    });

    bleno.on("disconnect", (clientAddress: string) => {
      console.log(`[BLE] Client disconnected: ${clientAddress}`);
    });

    process.on("SIGINT", () => {
      console.log("\n[BLE] Stopping...");
      bleno.stopAdvertising();
      bleno.disconnect();
      process.exit(0);
    });

    eventListenersSet = true;
  }

  if (bleno.state === "poweredOn") {
    startAdvertisingForConfig(config);
  }
}

function startAdvertisingForConfig(config: DeviceConfig): void {
  const services = config.services.map((svcConfig) => createService(svcConfig));
  bleno.startAdvertising(
    config.name,
    services.map((s) => s.uuid),
    (err?: Error | null) => {
      console.log("[BLE] startAdvertising callback");
      if (err) {
        console.error("Error starting advertising:", err);
        return;
      }

      console.log(`[BLE] Advertising started`);
      isAdvertising = true;
    }
  );
}
