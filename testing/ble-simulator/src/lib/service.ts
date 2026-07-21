import bleno from "@stoprocent/bleno";
import { createCharacteristic } from "./characteristic";
import type { ServiceConfig } from "../types";

export function createService(
  config: ServiceConfig
): InstanceType<typeof bleno.PrimaryService> {
  const characteristics = config.characteristics.map((charConfig) =>
    createCharacteristic(charConfig)
  );

  return new bleno.PrimaryService({
    uuid: config.uuid,
    characteristics: characteristics,
  });
}
