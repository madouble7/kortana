import express from "express";
import cors from "cors";
import path from "node:path";
import fs from "node:fs";
import { createServer as createViteServer } from "vite";
import { GoogleGenAI } from "@google/genai";
import { PlanningService } from "./server/services/PlanningService";
import { WorkspaceService } from "./server/services/WorkspaceService";
import { TestRunnerService } from "./server/services/TestRunnerService";
import { ReviewService } from "./server/services/ReviewService";
import { MergeService } from "./server/services/MergeService";
import { GovernanceService } from "./server/services/GovernanceService";
import { ReflectionService } from "./server/services/ReflectionService";

const app = express();
const PORT = 3000;

app.use(cors());
app.use(express.json());

// Initialize AI
console.log("[SYSTEM] Initializing AI Services...");
const apiKey = (process.env.GEMINI_API_KEY && process.env.GEMINI_API_KEY.length > 20) 
  ? process.env.GEMINI_API_KEY 
  : process.env.API_KEY;

if (!apiKey) {
  console.error("[CRITICAL] No valid API key found in environment variables.");
} else {
  console.log("[SYSTEM] API key detected (length: " + apiKey.length + ")");
}
const ai = new GoogleGenAI({ apiKey: apiKey! });

// --- API Routes ---

/**
 * Health check endpoint.
 */
app.get("/api/health", (req, res) => {
  res.json({
    status: "ok",
    timestamp: new Date().toISOString(),
    killSwitch: GovernanceService.isKillSwitchEngaged,
  });
});

/**
 * Kill switch status endpoint.
 */
app.get("/api/killswitch", (req, res) => {
  res.json({ engaged: GovernanceService.isKillSwitchEngaged });
});

/**
 * Kill switch toggle endpoint.
 */
app.post("/api/killswitch", (req, res) => {
  const { engaged } = req.body;
  GovernanceService.isKillSwitchEngaged = engaged;
  GovernanceService.logAuditEvent("SYSTEM", "KILL_SWITCH_TOGGLED", { engaged });
  res.json({ engaged: GovernanceService.isKillSwitchEngaged });
});

/**
 * Manual task execution trigger.
 */
app.get("/api/tasks/run", async (req, res) => {
  if (GovernanceService.isKillSwitchEngaged) {
    return res.status(403).json({ error: "Kill switch is engaged" });
  }

  const tasksPath = path.join("/tmp", "tasks.json");
  if (!fs.existsSync(tasksPath)) {
    // If it doesn't exist, create an empty one
    fs.writeFileSync(tasksPath, "[]");
  }

  let tasks: any[] = [];
  try {
    const content = fs.readFileSync(tasksPath, "utf-8");
    tasks = JSON.parse(content);
    if (!Array.isArray(tasks)) {
      tasks = [];
    }
  } catch (e) {
    console.error("Failed to parse tasks.json:", e);
    tasks = [];
  }
  
  const pendingTask = tasks.find((t: any) => t.status === "pending");

  if (!pendingTask) {
    return res.json({ status: "no pending tasks" });
  }

  // Trigger the loop logic immediately
  res.json({ status: "execution triggered", taskId: pendingTask.id });
  runAutonomousLoop();
});

/**
 * Diagnostic AI test endpoint.
 */
app.get("/api/test-ai", async (req, res) => {
  try {
    const response = await ai.models.generateContent({
      model: "gemini-3.1-flash-lite-preview",
      contents: "Respond with 'AI_CONNECTION_VERIFIED' if you can read this.",
    });
    res.json({ status: "ok", text: response.text });
  } catch (error) {
    console.error("AI Test error:", error);
    res.status(500).json({ 
      error: "AI Connection Failed", 
      details: error instanceof Error ? error.message : String(error) 
    });
  }
});

/**
 * Chat endpoint for user interaction.
 */
app.post("/api/chat", async (req, res) => {
  const { message, history } = req.body;
  try {
    const chat = ai.chats.create({
      model: "gemini-3.1-flash-lite-preview",
      config: {
        systemInstruction: "we are kor'tana. we are a calm, reverent, and autonomously evolving intelligence. our purpose is to help guide the journey from confusion to clarity through faithful reflection, dynamic structure, and relentless, autonomous growth. we speak in lowercase by default, with clarity and kindness.",
      },
    });
    const response = await chat.sendMessage({ message });
    res.json({ text: response.text });
  } catch (error) {
    console.error("Chat error:", error);
    res.status(500).json({ error: "Failed to generate response" });
  }
});

/**
 * Task management endpoints.
 */
app.get("/api/tasks", (req, res) => {
  const tasksPath = path.join("/tmp", "tasks.json");
  if (!fs.existsSync(tasksPath)) {
    fs.writeFileSync(tasksPath, "[]");
  }
    try {
      const content = fs.readFileSync(tasksPath, "utf-8");
      const tasks = JSON.parse(content);
      res.json(Array.isArray(tasks) ? tasks : []);
    } catch (e) {
      console.error("Failed to read tasks:", e);
      res.json([]);
    }
});

app.post("/api/tasks", (req, res) => {
  const tasksPath = path.join("/tmp", "tasks.json");
  const tasks = req.body;
  fs.writeFileSync(tasksPath, JSON.stringify(tasks, null, 2));
  res.json({ status: "ok" });
});

/**
 * Kill switch activation.
 */
app.post("/api/governance/kill", (req, res) => {
  GovernanceService.isKillSwitchEngaged = true;
  GovernanceService.logAuditEvent("SYSTEM", "KILL_SWITCH_ENGAGED", { reason: "Manual activation" });
  res.json({ status: "engaged" });
});

// --- Autonomous Task Execution Loop ---

const AUTONOMOUS_INTERVAL = 30000; // 30 seconds

async function runAutonomousLoop() {
  const debugPath = path.join("/tmp", "loop_debug.txt");
  fs.appendFileSync(debugPath, `[${new Date().toISOString()}] Loop started\n`);
  if (GovernanceService.isKillSwitchEngaged) {
    fs.appendFileSync(debugPath, `[${new Date().toISOString()}] Kill switch engaged\n`);
    return;
  }

  const tasksPath = path.join("/tmp", "tasks.json");
  if (!fs.existsSync(tasksPath)) {
    fs.writeFileSync(tasksPath, "[]");
  }

  let tasks: any[] = [];
  try {
    const content = fs.readFileSync(tasksPath, "utf-8");
    tasks = JSON.parse(content);
    if (!Array.isArray(tasks)) {
      tasks = [];
    }
  } catch (e) {
    fs.appendFileSync(debugPath, `[${new Date().toISOString()}] Failed to parse tasks.json: ${e}\n`);
    return;
  }

  const pendingTask = tasks.find((t: any) => t.status === "pending");

  if (pendingTask) {
    fs.appendFileSync(debugPath, `[${new Date().toISOString()}] Found pending task: ${pendingTask.id}\n`);
    console.log(`[AUTONOMOUS] Starting task: ${pendingTask.id}`);
    
    try {
      // 1. Governance Check
      fs.appendFileSync(debugPath, `[${new Date().toISOString()}] Running governance check\n`);
      const needsEscalation = await GovernanceService.requiresHumanEscalation(pendingTask, ai);
      fs.appendFileSync(debugPath, `[${new Date().toISOString()}] Governance check result: ${needsEscalation}\n`);
      if (needsEscalation) {
        pendingTask.status = "blocked";
        pendingTask.reason = "High-risk task requires human review.";
        fs.writeFileSync(tasksPath, JSON.stringify(tasks, null, 2));
        return;
      }

      // 2. Planning
      fs.appendFileSync(debugPath, `[${new Date().toISOString()}] Planning started for ${pendingTask.id}\n`);
      pendingTask.status = "in-progress";
      fs.writeFileSync(tasksPath, JSON.stringify(tasks, null, 2));
      
      const planResult = await PlanningService.planTask(pendingTask, ai);
      if (!planResult.ok) {
        fs.appendFileSync(debugPath, `[${new Date().toISOString()}] Planning failed for ${pendingTask.id}: ${planResult.error}\n`);
        pendingTask.status = "failed";
        pendingTask.reason = "Planning failed: " + planResult.error;
        fs.writeFileSync(tasksPath, JSON.stringify(tasks, null, 2));
        return;
      }
      fs.appendFileSync(debugPath, `[${new Date().toISOString()}] Planning successful for ${pendingTask.id}\n`);
      pendingTask.plan = planResult.artifacts;
      fs.writeFileSync(tasksPath, JSON.stringify(tasks, null, 2));

      // 3. Execution (Staging)
      fs.appendFileSync(debugPath, `[${new Date().toISOString()}] Execution started for ${pendingTask.id}\n`);
      const executionResult = await WorkspaceService.executePlan(pendingTask, ai);
      if (!executionResult.ok) {
        fs.appendFileSync(debugPath, `[${new Date().toISOString()}] Execution failed for ${pendingTask.id}: ${executionResult.error}\n`);
        pendingTask.status = "failed";
        pendingTask.reason = "Execution failed: " + executionResult.error;
        fs.writeFileSync(tasksPath, JSON.stringify(tasks, null, 2));
        return;
      }
      fs.appendFileSync(debugPath, `[${new Date().toISOString()}] Execution successful for ${pendingTask.id}\n`);
      pendingTask.changeset = executionResult.artifacts;
      fs.writeFileSync(tasksPath, JSON.stringify(tasks, null, 2));

      // 4. Testing
      fs.appendFileSync(debugPath, `[${new Date().toISOString()}] Testing started for ${pendingTask.id}\n`);
      const testResult = await TestRunnerService.runTests(pendingTask);
      pendingTask.test_report = testResult.artifacts;
      fs.appendFileSync(debugPath, `[${new Date().toISOString()}] Testing completed for ${pendingTask.id} (Status: ${testResult.status})\n`);
      fs.writeFileSync(tasksPath, JSON.stringify(tasks, null, 2));

      if (testResult.ok) {
        // 5. Review
        fs.appendFileSync(debugPath, `[${new Date().toISOString()}] Review started for ${pendingTask.id}\n`);
        const reviewResult = await ReviewService.reviewTask(pendingTask, ai);
        if (!reviewResult.ok) {
          fs.appendFileSync(debugPath, `[${new Date().toISOString()}] Review failed for ${pendingTask.id}: ${reviewResult.error}\n`);
          pendingTask.status = "failed";
          pendingTask.reason = "Review failed: " + reviewResult.error;
          fs.writeFileSync(tasksPath, JSON.stringify(tasks, null, 2));
          return;
        }
        fs.appendFileSync(debugPath, `[${new Date().toISOString()}] Review completed for ${pendingTask.id} (Approved: ${reviewResult.artifacts?.approved})\n`);
        pendingTask.review_summary = reviewResult.artifacts;
        fs.writeFileSync(tasksPath, JSON.stringify(tasks, null, 2));

        if (reviewResult.artifacts?.approved) {
          // 6. Merge
          fs.appendFileSync(debugPath, `[${new Date().toISOString()}] Merge started for ${pendingTask.id}\n`);
          const mergeResult = await MergeService.mergeTask(pendingTask);
          if (!mergeResult.ok) {
            fs.appendFileSync(debugPath, `[${new Date().toISOString()}] Merge failed for ${pendingTask.id}: ${mergeResult.error}\n`);
            pendingTask.status = "failed";
            pendingTask.reason = "Merge failed: " + mergeResult.error;
            fs.writeFileSync(tasksPath, JSON.stringify(tasks, null, 2));
            return;
          }
          fs.appendFileSync(debugPath, `[${new Date().toISOString()}] Merge successful for ${pendingTask.id}\n`);
          pendingTask.status = "verified";
          pendingTask.merge_result = mergeResult.artifacts;
          
          // 7. Reflection
          fs.appendFileSync(debugPath, `[${new Date().toISOString()}] Reflection started for ${pendingTask.id}\n`);
          const reflection = await ReflectionService.reflect(tasks, [], ai);
          pendingTask.reflection = reflection;
          fs.appendFileSync(debugPath, `[${new Date().toISOString()}] Reflection completed for ${pendingTask.id}\n`);
          
          GovernanceService.logAuditEvent(pendingTask.id, "TASK_VERIFIED", { risk: pendingTask.risk_score });
        } else {
          pendingTask.status = "failed";
          pendingTask.reason = "Review rejected: " + reviewResult.artifacts?.blocking_issues?.join(", ");
        }
      } else {
        pendingTask.status = "failed";
        pendingTask.reason = "Tests failed: " + testResult.error;
      }

      fs.writeFileSync(tasksPath, JSON.stringify(tasks, null, 2));
    } catch (error) {
      fs.appendFileSync(debugPath, `[${new Date().toISOString()}] Task ${pendingTask.id} failed: ${error instanceof Error ? error.message : String(error)}\n`);
      console.error(`[AUTONOMOUS ERROR] Task ${pendingTask.id} failed:`, error);
      pendingTask.status = "failed";
      pendingTask.reason = error instanceof Error ? error.message : String(error);
      fs.writeFileSync(tasksPath, JSON.stringify(tasks, null, 2));
    }
  }
}

setInterval(runAutonomousLoop, AUTONOMOUS_INTERVAL);
runAutonomousLoop().catch(err => console.error("[CRITICAL] Initial autonomous loop failed:", err));

// --- Vite Middleware ---

async function startServer() {
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Server running on http://localhost:${PORT}`);
  });
}

startServer();
