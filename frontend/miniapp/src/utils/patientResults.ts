import type { PatientResultDetails } from "../api/results";

export type PatientIndicatorView = {
  id: string;
  label: string;
  valueText: string;
  line: string;
};

function toNonEmptyString(value: unknown): string | null {
  if (value === null || value === undefined) {
    return null;
  }
  const text = String(value).trim();
  return text.length > 0 ? text : null;
}

function buildServiceMap(services: string[]): Map<string, string> {
  const serviceMap = new Map<string, string>();
  services.forEach((service) => {
    const [rawCode, rawHumanLabel] = service.split("•");
    if (!rawCode || !rawHumanLabel) {
      return;
    }
    const code = rawCode.trim();
    const humanLabel = rawHumanLabel.trim();
    if (code && humanLabel) {
      serviceMap.set(code, humanLabel);
    }
  });
  return serviceMap;
}

function resolveIndicatorCode(indicator: Record<string, unknown>): string | null {
  return (
    toNonEmptyString(indicator.parameter_name) ??
    toNonEmptyString(indicator.parameter_code) ??
    toNonEmptyString(indicator.code) ??
    toNonEmptyString(indicator.name)
  );
}

function resolveIndicatorValueText(indicator: Record<string, unknown>): string {
  const value =
    toNonEmptyString(indicator.parameter_value) ??
    toNonEmptyString(indicator.value) ??
    toNonEmptyString(indicator.result_value) ??
    "—";
  const unit =
    toNonEmptyString(indicator.measurement_unit) ??
    toNonEmptyString(indicator.unit) ??
    toNonEmptyString(indicator.measure_unit);
  return unit ? `${value} ${unit}` : value;
}

export function buildPatientIndicators(details: PatientResultDetails): PatientIndicatorView[] {
  const serviceMap = buildServiceMap(details.services);
  return details.indicators.map((indicator, index) => {
    const code = resolveIndicatorCode(indicator);
    const fallbackLabel = code ?? "Показатель";
    const label = code ? serviceMap.get(code) ?? fallbackLabel : fallbackLabel;
    const valueText = resolveIndicatorValueText(indicator);
    return {
      id: `${fallbackLabel}-${index}`,
      label,
      valueText,
      line: `${label}: ${valueText}`,
    };
  });
}
