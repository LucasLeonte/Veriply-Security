import { Bot, PaginatedBotsResponse } from "@/types/bot";

// Mock bots data
export const mockBots: Bot[] = [
    {
        id: "bot-123",
        name: "Customer Support Bot",
        description: "Handles customer inquiries and support tickets",
        confidence_threshold: 0.8,
        created_at: "2025-12-01T10:00:00Z",
        updated_at: "2025-12-10T15:30:00Z",
        status: "Ready",
        created_by: "user-1",
        tenant_id: "tenant-1",
        group_id: "group-1",
        doc_count: 12,
    },
    {
        id: "bot-456",
        name: "Product Documentation Bot",
        description: "Provides information about product features and specifications",
        confidence_threshold: 0.75,
        created_at: "2025-11-25T14:20:00Z",
        updated_at: "2025-12-09T11:15:00Z",
        status: "Ready",
        created_by: "user-1",
        tenant_id: "tenant-1",
        group_id: "group-1",
        doc_count: 8,
    },
    {
        id: "bot-789",
        name: "HR Policy Bot",
        description: "Answers questions about company policies and procedures",
        confidence_threshold: 0.85,
        created_at: "2025-11-20T09:45:00Z",
        updated_at: "2025-12-08T16:00:00Z",
        status: "Ready",
        created_by: "user-1",
        tenant_id: "tenant-1",
        group_id: "group-1",
        doc_count: 5,
    },
];

// Helper function to simulate API delay
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// Mock API functions
export const mockBotsApi = {
    async listBots(
        limit: number = 20,
        offset: number = 0,
        search?: string,
        sortBy: string = "name"
    ): Promise<PaginatedBotsResponse> {
        await delay(200);

        let filteredBots = [...mockBots];

        if (search) {
            const searchLower = search.toLowerCase();
            filteredBots = filteredBots.filter(bot =>
                bot.name.toLowerCase().includes(searchLower) ||
                bot.description?.toLowerCase().includes(searchLower)
            );
        }

        // Simple sorting
        if (sortBy === "name") {
            filteredBots.sort((a, b) => a.name.localeCompare(b.name));
        } else if (sortBy === "created_at") {
            filteredBots.sort((a, b) => 
                new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
            );
        }

        const total = filteredBots.length;
        const paginatedBots = filteredBots.slice(offset, offset + limit);

        return {
            bots: paginatedBots,
            total_count: total,
            limit,
            offset,
        };
    },

    async getBot(botId: string): Promise<Bot> {
        await delay(150);
        
        const bot = mockBots.find(b => b.id === botId);
        if (!bot) {
            throw new Error("Bot not found");
        }

        return bot;
    },

    async createBot(data: { name: string; description?: string; confidence_threshold?: number }): Promise<Bot> {
        await delay(300);

        const newBot: Bot = {
            id: `bot-${Date.now()}`,
            name: data.name,
            description: data.description,
            confidence_threshold: data.confidence_threshold || 0.8,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            status: "Empty",
            created_by: "user-1",
            tenant_id: "tenant-1",
            group_id: "group-1",
            doc_count: 0,
        };

        mockBots.push(newBot);
        return newBot;
    },

    async updateBot(botId: string, data: Partial<Bot>): Promise<Bot> {
        await delay(250);

        const bot = mockBots.find(b => b.id === botId);
        if (!bot) {
            throw new Error("Bot not found");
        }

        Object.assign(bot, data, { updated_at: new Date().toISOString() });
        return bot;
    },

    async deleteBot(botId: string): Promise<void> {
        await delay(200);

        const index = mockBots.findIndex(b => b.id === botId);
        if (index === -1) {
            throw new Error("Bot not found");
        }

        mockBots.splice(index, 1);
    },

    async duplicateBot(botId: string, newName: string): Promise<Bot> {
        await delay(400);

        const originalBot = mockBots.find(b => b.id === botId);
        if (!originalBot) {
            throw new Error("Bot not found");
        }

        const duplicatedBot: Bot = {
            ...originalBot,
            id: `bot-${Date.now()}`,
            name: newName,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
        };

        mockBots.push(duplicatedBot);
        return duplicatedBot;
    },
};
