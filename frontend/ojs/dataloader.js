// ojs/dataloader.js - Just loads data
// Usage: import {loadData} from "./ojs/dataloader.js"
//        d = loadData()
//        Then: d.pg, d.pas, d.pv, etc.

// import { FileAttachment } from "@observablehq/stdlib";

async function loadCSV(path) {
  // const d3 = await import("https://cdn.jsdelivr.net/npm/d3@7/+esm");
  // const response = await fetch(path);
  // const text = await response.text();
  // return d3.csvParse(text, d3.autoType);
  return await FileAttachment(path).csv({typed: true});
}

export async function loadData() {
  const basePath = "./02-process-output/tabular/processed/";

  const [pg, pas, rwi_area, uba, uba_area, lc, pug, pv, pv_area,
         aq_area, summer_area, ndvi_area, fu, pu, cu, comb,
         e, s, ls_area, l_area, fwi] = await Promise.all([
    loadCSV(basePath + "pg.csv"),
    loadCSV(basePath + "pas.csv"),
    loadCSV(basePath + "rwi_area.csv"),
    loadCSV(basePath + "uba.csv"),
    loadCSV(basePath + "uba_area.csv"),
    loadCSV(basePath + "lc.csv"),
    loadCSV(basePath + "pug.csv"),
    loadCSV(basePath + "pv.csv"),
    loadCSV(basePath + "pv_area.csv"),
    loadCSV(basePath + "aq_area.csv"),
    loadCSV(basePath + "summer_area.csv"),
    loadCSV(basePath + "ndvi_area.csv"),
    loadCSV(basePath + "fu.csv"),
    loadCSV(basePath + "pu.csv"),
    loadCSV(basePath + "cu.csv"),
    loadCSV(basePath + "comb.csv"),
    loadCSV(basePath + "e.csv"),
    loadCSV(basePath + "s.csv"),
    loadCSV(basePath + "ls_area.csv"),
    loadCSV(basePath + "l_area.csv"),
    loadCSV(basePath + "fwi.csv")
  ]);

  const fe = [{begin_year: 1995, begin_month: 9, DISPLACED: 95000, severity: "Large event", line1: "SEPTEMBER 1995", line2: "95,000 displaced", line3: ""}];

  return {pg, pas, rwi_area, uba, uba_area, lc, pug, pv, pv_area, aq_area, summer_area, ndvi_area, fu, pu, cu, comb, e, s, ls_area, l_area, fwi, fe};
}
