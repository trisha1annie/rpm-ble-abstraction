export function encodeSFloat(value: number): number {
  if (value === 0) return 0x0000;

  const mantissa = Math.round(value * 10) & 0x0fff;
  const exponent = 0xf;

  return (exponent << 12) | mantissa;
}
