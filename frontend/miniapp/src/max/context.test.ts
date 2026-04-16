import { getMaxContext } from "./context";

describe("MAX context", () => {
  afterEach(() => {
    window.WebApp = undefined;
  });

  it("корректно определяет fallback-вариант вне MAX", () => {
    window.WebApp = undefined;

    const context = getMaxContext();

    expect(context.isInsideMax).toBe(false);
    expect(context.hasInitData).toBe(false);
    expect(context.hasUser).toBe(false);
    expect(context.hasStartParam).toBe(false);
    expect(context.patientId).toBeNull();
  });

  it("читает initData/initDataUnsafe и user.id внутри MAX", () => {
    window.WebApp = {
      initData: "signed-payload",
      initDataUnsafe: {
        start_param: "result:card-77",
        user: { id: 777 },
      },
      platform: "max-mobile",
      version: "2.0",
    };

    const context = getMaxContext();

    expect(context.isInsideMax).toBe(true);
    expect(context.hasInitData).toBe(true);
    expect(context.hasUser).toBe(true);
    expect(context.hasStartParam).toBe(true);
    expect(context.initData).toBe("signed-payload");
    expect(context.startParam).toBe("result:card-77");
    expect(context.patientId).toBe("777");
    expect(context.platform).toBe("max-mobile");
    expect(context.version).toBe("2.0");
  });
});
