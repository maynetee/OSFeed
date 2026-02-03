import { describe, it, expect } from "vitest";
import { cn } from "../cn";

describe("cn", () => {
  it("should merge class names", () => {
    expect(cn("class1", "class2")).toBe("class1 class2");
  });

  it("should handle conditional classes", () => {
    expect(cn("base", true && "conditional")).toBe("base conditional");
    expect(cn("base", false && "conditional")).toBe("base");
  });

  it("should handle undefined and null values", () => {
    expect(cn("base", undefined, "other")).toBe("base other");
    expect(cn("base", null, "other")).toBe("base other");
  });

  it("should handle empty strings", () => {
    expect(cn("base", "", "other")).toBe("base other");
    expect(cn("", "only")).toBe("only");
  });

  it("should merge Tailwind classes correctly", () => {
    // twMerge should handle conflicting Tailwind classes
    expect(cn("p-4", "p-2")).toBe("p-2");
    expect(cn("text-red-500", "text-blue-500")).toBe("text-blue-500");
  });

  it("should handle arrays of classes", () => {
    expect(cn(["class1", "class2"])).toBe("class1 class2");
    expect(cn(["class1"], "class2")).toBe("class1 class2");
  });

  it("should handle object notation", () => {
    expect(cn({ active: true, disabled: false })).toBe("active");
    expect(cn({ "px-4": true, "py-2": true })).toBe("px-4 py-2");
  });

  it("should handle mixed input types", () => {
    expect(cn("base", ["array", "classes"], { active: true }, "end")).toBe(
      "base array classes active end"
    );
  });

  it("should handle no arguments", () => {
    expect(cn()).toBe("");
  });

  it("should handle complex Tailwind merge scenarios", () => {
    // Last class should win for conflicting properties
    expect(cn("px-4 py-2", "px-6")).toBe("py-2 px-6");
    expect(cn("rounded-lg", "rounded-none")).toBe("rounded-none");
  });

  it("should preserve non-conflicting Tailwind classes", () => {
    expect(cn("p-4 text-red-500", "m-2 bg-blue-500")).toContain("p-4");
    expect(cn("p-4 text-red-500", "m-2 bg-blue-500")).toContain("text-red-500");
    expect(cn("p-4 text-red-500", "m-2 bg-blue-500")).toContain("m-2");
    expect(cn("p-4 text-red-500", "m-2 bg-blue-500")).toContain("bg-blue-500");
  });

  it("should handle responsive Tailwind classes", () => {
    expect(cn("md:p-4", "lg:p-6")).toBe("md:p-4 lg:p-6");
    expect(cn("md:p-4", "md:p-6")).toBe("md:p-6");
  });

  it("should handle pseudo-class variants", () => {
    expect(cn("hover:bg-blue-500", "hover:bg-red-500")).toBe("hover:bg-red-500");
    expect(cn("hover:bg-blue-500", "focus:bg-red-500")).toBe(
      "hover:bg-blue-500 focus:bg-red-500"
    );
  });

  it("should handle dark mode classes", () => {
    expect(cn("dark:bg-black", "dark:bg-white")).toBe("dark:bg-white");
    expect(cn("bg-white dark:bg-black", "dark:bg-gray-900")).toBe(
      "bg-white dark:bg-gray-900"
    );
  });

  it("should work with common component patterns", () => {
    // Button component pattern
    const baseButton = "px-4 py-2 rounded font-medium";
    const variant = "bg-blue-500 text-white";
    expect(cn(baseButton, variant)).toContain("px-4");
    expect(cn(baseButton, variant)).toContain("bg-blue-500");

    // Conditional variant
    const isDisabled = false;
    expect(cn(baseButton, isDisabled && "opacity-50 cursor-not-allowed")).toBe(
      baseButton
    );
  });

  it("should handle deeply nested conditionals", () => {
    const size = "large";
    const disabled = false;

    expect(
      cn(
        "base",
        size === "small" && "text-sm",
        size === "large" && "text-lg",
        disabled && "opacity-50"
      )
    ).toBe("base text-lg");
  });

  it("should handle arbitrary values", () => {
    expect(cn("p-[20px]", "m-[10px]")).toBe("p-[20px] m-[10px]");
  });
});
