export interface CharacteristicConfig {
  uuid: string;
  name: string;
  properties: string[];
  initial?: string;
  encoder?: {
    type: string;
  };
}

export interface ServiceConfig {
  uuid: string;
  characteristics: CharacteristicConfig[];
}

export interface DeviceConfig {
  name: string;
  displayName?: string;
  services: ServiceConfig[];
}

export interface CharHandle {
  config: CharacteristicConfig;
  value: Buffer;
  updateValueCallback: ((data: Buffer) => void) | null;
}

export type Registry = Record<string, CharHandle>;
