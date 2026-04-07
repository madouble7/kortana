import { GoogleGenAI } from "@google/genai";
try {
  new GoogleGenAI({ apiKey: "" });
  console.log("SUCCESS");
} catch (e) {
  console.log("ERROR", e);
}
