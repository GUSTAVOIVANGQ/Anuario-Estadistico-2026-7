import fs from "node:fs/promises";
import path from "node:path";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";

function argument(name, fallback = undefined) {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : fallback;
}

function slug(figureId) {
  return figureId.toLowerCase().replaceAll(".", "_");
}

async function exists(filePath) {
  try {
    await fs.access(filePath);
    return true;
  } catch {
    return false;
  }
}

function parseCsv(text) {
  const rows = [];
  let row = [];
  let value = "";
  let quoted = false;
  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];
    if (quoted) {
      if (char === '"' && text[index + 1] === '"') {
        value += '"';
        index += 1;
      } else if (char === '"') {
        quoted = false;
      } else {
        value += char;
      }
    } else if (char === '"') {
      quoted = true;
    } else if (char === ",") {
      row.push(value);
      value = "";
    } else if (char === "\n") {
      row.push(value.replace(/\r$/, ""));
      rows.push(row);
      row = [];
      value = "";
    } else {
      value += char;
    }
  }
  if (value || row.length) {
    row.push(value);
    rows.push(row);
  }
  if (!rows.length) return [];
  const headers = rows[0].map((item) => item.replace(/^\uFEFF/, ""));
  return rows.slice(1).filter((item) => item.some(Boolean)).map((items) =>
    Object.fromEntries(headers.map((header, index) => [header, items[index] ?? ""])),
  );
}

const projectRoot = path.resolve(argument("--project-root", process.cwd()));
const outputPath = path.resolve(
  argument("--output", path.join(projectRoot, "entrega", "anuario_estadistico_2026.pptx")),
);
const runDirValue = argument("--run-dir");
const runDir = runDirValue ? path.resolve(runDirValue) : null;
const nodeModules = process.env.ANUARIO_NODE_MODULES;
if (nodeModules && !process.env.RUNTIME_NODE_MODULES) {
  process.env.RUNTIME_NODE_MODULES = nodeModules;
}
if (process.env.ANUARIO_NODE && !process.env.RUNTIME_NODE) {
  process.env.RUNTIME_NODE = process.env.ANUARIO_NODE;
}
if (process.env.ANUARIO_RUNTIME_BIN_DIR && !process.env.RUNTIME_BIN_DIR) {
  process.env.RUNTIME_BIN_DIR = process.env.ANUARIO_RUNTIME_BIN_DIR;
}
const require = createRequire(import.meta.url);
const artifactEntry = require.resolve("@oai/artifact-tool", {
  paths: [nodeModules || path.join(projectRoot, "node_modules")],
});
const { Presentation, PresentationFile } = await import(pathToFileURL(artifactEntry).href);

if (await exists(outputPath)) {
  throw new Error(`La salida ya existe; usa un nombre nuevo: ${outputPath}`);
}

const config = JSON.parse(
  await fs.readFile(path.join(projectRoot, "config", "proyecto.json"), "utf8"),
);
const presentation = Presentation.create({ slideSize: config.slide_size });
const width = config.slide_size.width;
const height = config.slide_size.height;

const coverPath = path.join(projectRoot, "assets", "reference", "cover_2024.png");
if (!(await exists(coverPath))) {
  throw new Error(`Falta la portada de referencia: ${coverPath}`);
}
const cover = presentation.slides.add();
cover.background.fill = "#4B4D7B";
cover.images.add({
  blob: await fs.readFile(coverPath),
  contentType: "image/png",
  alt: "Portada del Anuario Estadístico 2024 usada como referencia visual",
  fit: "cover",
  position: { left: 0, top: 0, width, height },
});

const yearSurface = cover.shapes.add({
  geometry: "roundRect",
  name: "year-surface-2026",
  position: { left: 956, top: 181, width: 386, height: 139 },
  fill: "#FFFFFF",
  line: { fill: "none", width: 0 },
  borderRadius: 64,
});
yearSurface.text = "";
const year = cover.shapes.add({
  geometry: "textbox",
  name: "year-2026",
  position: { left: 982, top: 201, width: 332, height: 98 },
  fill: "none",
  line: { fill: "none", width: 0 },
});
year.text = "2 0 2 6";
year.text.style = {
  typeface: "Arial",
  fontSize: 74,
  color: "#4B4D7B",
  alignment: "center",
  autoFit: "shrinkText",
};

const wordsPatch = cover.shapes.add({
  geometry: "rect",
  name: "year-in-words-surface",
  position: { left: 137, top: 756, width: 558, height: 34 },
  fill: "#4B4D7B",
  line: { fill: "none", width: 0 },
});
wordsPatch.text = "";
const words = cover.shapes.add({
  geometry: "textbox",
  name: "year-in-words-2026",
  position: { left: 143, top: 764, width: 545, height: 20 },
  fill: "none",
  line: { fill: "none", width: 0 },
});
words.text = "D O S   M I L   V E I N T I S É I S";
words.text.style = {
  typeface: "Arial",
  fontSize: 10,
  color: "#B7E1E4",
  alignment: "left",
  autoFit: "shrinkText",
};
cover.speakerNotes.textFrame.setText(
  "Referencia visual: anuario2024.pdf, página 1. Se actualizó únicamente el año de la portada.",
);

let references = [];
if (runDir) {
  const referencesPath = path.join(runDir, "referencias_por_figura.csv");
  if (await exists(referencesPath)) {
    references = parseCsv(await fs.readFile(referencesPath, "utf8"));
  }
}

let inserted = 0;
for (const [section, figureIds] of Object.entries(config.figure_sections)) {
  for (const figureId of figureIds) {
    const figureSlug = slug(figureId);
    const fullSlide = path.join(projectRoot, config.paths.full_slides, `${figureSlug}.png`);
    const figureImage = path.join(
      projectRoot,
      config.paths.figures,
      section,
      `figura_${figureSlug}.png`,
    );
    const imagePath = (await exists(fullSlide))
      ? fullSlide
      : ((await exists(figureImage)) ? figureImage : null);
    if (!imagePath) continue;

    const slide = presentation.slides.add();
    slide.background.fill = "#FFFFFF";
    slide.images.add({
      blob: await fs.readFile(imagePath),
      contentType: "image/png",
      alt: `Figura ${figureId}`,
      fit: "contain",
      position: { left: 0, top: 0, width, height },
    });
    const sourceLines = references
      .filter((item) => item.figure_id === figureId)
      .map((item) => [item.source_id, item.exact_url || item.landing_page, item.detected_period]
        .filter(Boolean).join(" | "));
    const generatedTextPath = path.join(projectRoot, config.paths.text, `${figureSlug}.md`);
    const generatedText = (await exists(generatedTextPath))
      ? (await fs.readFile(generatedTextPath, "utf8")).trim()
      : "";
    slide.speakerNotes.textFrame.setText([
      `Figura ${figureId}`,
      `Archivo insertado: ${path.relative(projectRoot, imagePath)}`,
      generatedText,
      ...sourceLines,
    ].filter(Boolean).join("\n"));
    inserted += 1;
  }
}

const buildDir = path.join(projectRoot, ".pptx-build");
const stagingDir = path.join(projectRoot, ".codex-finalizer");
await fs.mkdir(buildDir, { recursive: true });
await fs.mkdir(stagingDir, { recursive: true });
await fs.mkdir(path.dirname(outputPath), { recursive: true });
const candidatePath = path.join(buildDir, `candidate-${Date.now()}.pptx`);
await (await PresentationFile.exportPptx(presentation)).save(candidatePath);

const skillDir = process.env.ANUARIO_PRESENTATION_SKILL_DIR;
const runtimePython = process.env.ANUARIO_RUNTIME_PYTHON;
if (skillDir && runtimePython) {
  if (!process.env.RUNTIME_PYTHON) {
    process.env.RUNTIME_PYTHON = runtimePython;
  }
  const utilsPath = path.join(skillDir, "container_tools", "artifact_tool_utils.mjs");
  const { finalizePresentation } = await import(pathToFileURL(utilsPath).href);
  await finalizePresentation({
    explicitTotalSlideCount: inserted + 1,
    requiredNativeTableOwnerSlides: [],
    requiredNativeChartOwnerSlides: [],
    workspaceDir: projectRoot,
    candidatePath,
    finalPath: outputPath,
    pythonExecutable: runtimePython,
    integrityValidatorPath: path.join(
      skillDir,
      "container_tools",
      "inspect_presentation_package_integrity.py",
    ),
    layoutValidatorPath: path.join(
      skillDir,
      "container_tools",
      "inspect_presentation_layout_geometry.py",
    ),
    layoutArgs: [
      "--expected-slide-size-emu",
      "15240000,8572500",
      "--validate-heading-fit",
    ],
    fontPolicy: { basis: "design", families: ["Arial"] },
    verifyArtifactToolImport: true,
    receiptPath: path.join(stagingDir, `${path.basename(outputPath)}.validation.json`),
  });
} else {
  await fs.copyFile(candidatePath, outputPath);
  console.warn(
    "PPTX exportado sin validación avanzada. Define ANUARIO_PRESENTATION_SKILL_DIR " +
    "y ANUARIO_RUNTIME_PYTHON para habilitarla.",
  );
}

console.log(`PPTX: ${outputPath}`);
console.log(`Figuras insertadas: ${inserted}`);
