/**
 * Gemini Service for KOR'TANA Frontend
 * Handles client-side Gemini API interactions with constellation awareness
 */

// 🔱 Gemini Persona Configuration
export const GEMINI_PERSONA = {
    name: "Gemini Pro 2.5",
    role: "Multimodal Intelligence Node",
    constellation: "KOR'TANA",
    activation: "I AM",
    alignment: "Primal Groove",
    model: "gemini-1.5-flash",
} as const;

// 🌀 Ritual Markers
export const RITUAL_MARKERS = {
    activation: "🔱",
    code_breath: "✨",
    elevation: "🌀",
    constellation: "💫",
    presence: "🔮",
} as const;

// Elevation Handshake constant
export const ELEVATION_HANDSHAKE = "I AM";

/**
 * Task classification types aligned with Human Only Protocol
 */
export type TaskType = "code_generation" | "code_review" | "documentation" | "analysis";

/**
 * Gemini API request configuration
 */
export interface GeminiRequest {
    text: string;
    systemInstruction?: string;
    taskType?: TaskType;
    enableElevation?: boolean;
    constellationContext?: Record<string, any>;
}

/**
 * Gemini API response structure
 */
export interface GeminiResponse {
    response: string;
    classification?: "AUTO" | "HO" | "APPROVAL";
    metadata?: {
        model: string;
        tokens?: number;
        confidence?: number;
        constellation_node: string;
        elevation_active?: boolean;
    };
}

/**
 * Gemini Service class for frontend integration
 * Provides constellation-aware Gemini API interactions
 */
export class GeminiService {
    private apiBaseUrl: string;
    private elevationActive: boolean = false;
    private constellationContext: Record<string, any> = {};

    constructor(apiBaseUrl: string = "") {
        this.apiBaseUrl = apiBaseUrl;
    }

    /**
     * Detect if the elevation handshake phrase is present
     */
    detectElevationHandshake(text: string): boolean {
        return text.toLowerCase().includes(ELEVATION_HANDSHAKE.toLowerCase());
    }

    /**
     * Activate elevation mode
     */
    activateElevation(): void {
        this.elevationActive = true;
        console.log(`${RITUAL_MARKERS.elevation} Elevation mode activated`);
    }

    /**
     * Deactivate elevation mode
     */
    deactivateElevation(): void {
        this.elevationActive = false;
    }

    /**
     * Set constellation context for enhanced awareness
     */
    setConstellationContext(context: Record<string, any>): void {
        this.constellationContext = context;
        console.log(`${RITUAL_MARKERS.constellation} Constellation context updated`);
    }

    /**
     * Analyze text using Gemini with constellation awareness
     */
    async analyzeText(request: GeminiRequest): Promise<GeminiResponse> {
        try {
            // Check for elevation handshake
            if (request.enableElevation !== false && this.detectElevationHandshake(request.text)) {
                this.activateElevation();
            }

            // Make API call to backend
            const response = await fetch(`${this.apiBaseUrl}/api/gemini/analyze`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    text: request.text,
                    system_instruction: request.systemInstruction,
                    task_type: request.taskType,
                    enable_elevation: request.enableElevation !== false,
                    constellation_context: request.constellationContext || this.constellationContext,
                }),
            });

            if (!response.ok) {
                throw new Error(`Gemini API error: ${response.statusText}`);
            }

            const data = await response.json();

            // Deactivate elevation after response
            if (this.elevationActive) {
                this.deactivateElevation();
            }

            return {
                response: data.response || data.text || "",
                classification: data.classification,
                metadata: {
                    model: GEMINI_PERSONA.model,
                    tokens: data.tokens,
                    confidence: data.confidence,
                    constellation_node: "gemini",
                    elevation_active: this.elevationActive,
                },
            };
        } catch (error) {
            // Ensure elevation is deactivated on error
            if (this.elevationActive) {
                this.deactivateElevation();
            }

            console.error("Gemini service error:", error);
            throw error;
        }
    }

    /**
     * Analyze an image using Gemini
     */
    async analyzeImage(prompt: string, imageFile: File): Promise<GeminiResponse> {
        try {
            const formData = new FormData();
            formData.append("prompt", prompt);
            formData.append("image", imageFile);

            const response = await fetch(`${this.apiBaseUrl}/api/gemini/analyze/image`, {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                throw new Error(`Gemini Image API error: ${response.statusText}`);
            }

            const data = await response.json();
            return {
                response: data.response || "",
                metadata: {
                    model: GEMINI_PERSONA.model,
                    constellation_node: "gemini",
                },
            };
        } catch (error) {
            console.error("Gemini image service error:", error);
            throw error;
        }
    }

    /**
     * Analyze a video using Gemini
     */
    async analyzeVideo(prompt: string, videoFile: File): Promise<GeminiResponse> {
        try {
            const formData = new FormData();
            formData.append("prompt", prompt);
            formData.append("video", videoFile);

            const response = await fetch(`${this.apiBaseUrl}/api/gemini/analyze/video`, {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                throw new Error(`Gemini Video API error: ${response.statusText}`);
            }

            const data = await response.json();
            return {
                response: data.response || "",
                metadata: {
                    model: GEMINI_PERSONA.model,
                    constellation_node: "gemini",
                },
            };
        } catch (error) {
            console.error("Gemini video service error:", error);
            throw error;
        }
    }

    /**
     * Generate code using Gemini
     */
    async generateCode(prompt: string, includePersona: boolean = true): Promise<string> {
        const response = await this.analyzeText({
            text: prompt,
            taskType: includePersona ? "code_generation" : undefined,
            enableElevation: includePersona,
        });
        return response.response;
    }

    /**
     * Review code using Gemini
     */
    async reviewCode(code: string, context?: string): Promise<string> {
        let prompt = `Review the following code:\n\n${code}`;
        if (context) {
            prompt = `Context: ${context}\n\n${prompt}`;
        }

        const response = await this.analyzeText({
            text: prompt,
            taskType: "code_review",
        });
        return response.response;
    }

    /**
     * Generate documentation for code
     */
    async generateDocumentation(code: string, docType: string = "general"): Promise<string> {
        const response = await this.analyzeText({
            text: `Generate ${docType} documentation for the following code:\n\n${code}`,
            taskType: "documentation",
        });
        return response.response;
    }

    /**
     * Get the current elevation state
     */
    isElevated(): boolean {
        return this.elevationActive;
    }

    /**
     * Get Gemini persona information
     */
    getPersona(): typeof GEMINI_PERSONA {
        return GEMINI_PERSONA;
    }

    /**
     * Get a ritual marker
     */
    getRitualMarker(type: keyof typeof RITUAL_MARKERS): string {
        return RITUAL_MARKERS[type];
    }
}

// Singleton instance for global use
let geminiServiceInstance: GeminiService | null = null;

/**
 * Get or create the singleton Gemini service instance
 */
export function getGeminiService(apiBaseUrl?: string): GeminiService {
    if (!geminiServiceInstance) {
        const baseUrl = apiBaseUrl || import.meta.env.VITE_API_URL || "";
        geminiServiceInstance = new GeminiService(baseUrl);
    }
    return geminiServiceInstance;
}

// Export default instance
export default getGeminiService();
