import { buildPatientIndicators } from "./patientResults";
import type { PatientResultDetails } from "../api/results";

function makeDetails(payload: Partial<PatientResultDetails>): PatientResultDetails {
  return {
    result_id: "r-1",
    title: "Тест",
    date: "2026-04-20",
    status: "Готов",
    has_pdf: true,
    lab_name: "Лаб.",
    clinic_name: "Клиника",
    services: [],
    sections: [],
    indicators: [],
    pdf_open_url: "/patient/results/r-1/pdf",
    pdf_download_url: "/patient/results/r-1/pdf",
    ...payload,
  };
}

describe("buildPatientIndicators", () => {
  it("использует человекочитаемое название после символа •", () => {
    const details = makeDetails({
      services: ["K • Калий (К+)", "Mg • Магний (кровь, фотометрия)"],
      indicators: [
        { parameter_name: "K", parameter_value: "4.2", measurement_unit: "ммоль/л" },
        { parameter_name: "Mg", parameter_value: "0.83", measurement_unit: "ммоль/л" },
      ],
    });

    const view = buildPatientIndicators(details);
    expect(view[0].line).toBe("Калий (К+): 4.2 ммоль/л");
    expect(view[1].line).toBe("Магний (кровь, фотометрия): 0.83 ммоль/л");
  });

  it("использует fallback на parameter_name при отсутствии matching service", () => {
    const details = makeDetails({
      services: ["Na • Натрий"],
      indicators: [{ parameter_name: "PRL", parameter_value: "53.8 ++", measurement_unit: "нг/мл" }],
    });

    const view = buildPatientIndicators(details);
    expect(view[0].line).toBe("PRL: 53.8 ++ нг/мл");
  });

  it("использует fallback без единицы измерения, если unit отсутствует", () => {
    const details = makeDetails({
      services: ["PROLACTIN • Пролактин"],
      indicators: [{ parameter_name: "PROLACTIN", parameter_value: "53.8 ++" }],
    });

    const view = buildPatientIndicators(details);
    expect(view[0].line).toBe("Пролактин: 53.8 ++");
  });
});
