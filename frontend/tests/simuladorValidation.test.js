import test from "node:test";
import assert from "node:assert/strict";
import { validarMonto } from "../src/utils/simuladorValidation.js";

test("acepta cero, coma decimal y el límite RIMPE", () => {
  assert.deepEqual(validarMonto("0"), { monto: 0 });
  assert.deepEqual(validarMonto(" 35000,50 "), { monto: 35000.5 });
  assert.deepEqual(validarMonto("300000.00"), { monto: 300000 });
});

test("rechaza entradas que no deben convertirse en una cuota cero", () => {
  for (const entrada of ["", "-1", "1.234,56", "100.001", "1e3", "300000,01"]) {
    assert.ok(validarMonto(entrada).error, `Se aceptó indebidamente: ${entrada}`);
  }
});
