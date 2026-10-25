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

  notification?: {
    enabled: boolean;
    rate_hz: number;
    characteristic: string;
    values: number[];

    faults?: {
      jitter_ms?: number;
      dropout_start_after_ms?:number;
      jitter_start_after_ms?: number;
      dropout_duration_ms?: number;
    };
  };
}

export interface CharHandle {
  config: CharacteristicConfig;
  value: Buffer;
  updateValueCallback: ((data: Buffer) => void) | null;
}

export type Registry = Record<string, CharHandle>;
