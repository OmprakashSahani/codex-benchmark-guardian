const SCIENTIFIC_SMALL = 1e-6;
const SCIENTIFIC_LARGE = 1e9;

function formatExponential(value: number, fractionDigits: number) {
  const [mantissa, exponent] = value.toExponential(fractionDigits).split("e");
  return `${mantissa.replace(/\.0+$|(?<=\.[0-9]*[1-9])0+$/, "")}e${exponent}`;
}

function formatWithPrecision(value: number, significantDigits: number) {
  const absolute = Math.abs(value);
  if (absolute !== 0 && (absolute < SCIENTIFIC_SMALL || absolute >= SCIENTIFIC_LARGE)) {
    return formatExponential(value, Math.min(significantDigits - 1, 16));
  }
  return new Intl.NumberFormat("en-US", {
    maximumSignificantDigits: significantDigits,
    useGrouping: true,
  }).format(value);
}

export function formatNumber(value: number) {
  if (!Number.isFinite(value)) return "—";
  if (Object.is(value, -0) || value === 0) return "0";
  return formatWithPrecision(value, 12);
}

export function formatNumberPair(first: number, second: number): [string, string] {
  if (!Number.isFinite(first) || !Number.isFinite(second) || first === second) {
    return [formatNumber(first), formatNumber(second)];
  }

  for (let precision = 12; precision <= 17; precision += 1) {
    const formattedFirst = formatWithPrecision(first, precision);
    const formattedSecond = formatWithPrecision(second, precision);
    if (formattedFirst !== formattedSecond) return [formattedFirst, formattedSecond];
  }

  return [formatExponential(first, 16), formatExponential(second, 16)];
}

export function formatPercentage(value: number) {
  if (!Number.isFinite(value)) return "—";
  if (Object.is(value, -0) || value === 0) return "0.00%";

  const absolute = Math.abs(value);
  const sign = value > 0 ? "+" : "-";
  if (absolute < SCIENTIFIC_SMALL || absolute >= SCIENTIFIC_LARGE) {
    return `${sign}${formatExponential(absolute, 4)}%`;
  }

  const fractionDigits = absolute < 0.01
    ? Math.min(12, Math.max(4, -Math.floor(Math.log10(absolute)) + 3))
    : 2;
  return `${sign}${absolute.toFixed(fractionDigits)}%`;
}
