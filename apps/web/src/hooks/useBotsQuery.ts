import { useState, useCallback, useEffect } from "react";
import {
    Bot,
    CreateBotInput,
    UpdateBotInput,
    PaginatedBotsResponse,
} from "@/types/bot";
import { botsApi } from "@/lib/api/bots";

export function useBotsQuery(
    groupId: string | null,
    limit: number = 20,
    offset: number = 0,
    search?: string,
    sortBy: string = "name"
) {
    const [data, setData] = useState<PaginatedBotsResponse | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<Error | null>(null);

    const refetch = useCallback(async () => {
        if (!groupId) {
            setData(null);
            return;
        }

        setIsLoading(true);
        setError(null);
        try {
            const result = await botsApi.listBots(
                groupId,
                limit,
                offset,
                search,
                sortBy
            );
            setData(result);
        } catch (err) {
            setError(
                err instanceof Error ? err : new Error("Failed to fetch bots")
            );
        } finally {
            setIsLoading(false);
        }
    }, [groupId, limit, offset, search, sortBy]);

    useEffect(() => {
        refetch();
    }, [refetch]);

    return { data, isLoading, error, refetch };
}

export function useBotQuery(groupId: string | null, botId: string) {
    const [data, setData] = useState<Bot | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<Error | null>(null);

    const refetch = useCallback(async () => {
        if (!groupId || !botId) {
            setData(null);
            return;
        }

        setIsLoading(true);
        setError(null);
        try {
            const result = await botsApi.getBotDetails(groupId, botId);
            setData(result);
        } catch (err) {
            setError(
                err instanceof Error ? err : new Error("Failed to fetch bot")
            );
        } finally {
            setIsLoading(false);
        }
    }, [groupId, botId]);

    useEffect(() => {
        if (groupId && botId) {
            refetch();
        }
    }, [groupId, botId, refetch]);

    return { data, isLoading, error, refetch };
}

export function useCreateBot() {
    const [isPending, setIsPending] = useState(false);
    const [error, setError] = useState<Error | null>(null);

    const mutate = useCallback(
        async (botData: CreateBotInput): Promise<Bot> => {
            setIsPending(true);
            setError(null);
            try {
                const result = await botsApi.createBot(botData);
                return result;
            } catch (err) {
                const error =
                    err instanceof Error
                        ? err
                        : new Error("Failed to create bot");
                setError(error);
                throw error;
            } finally {
                setIsPending(false);
            }
        },
        []
    );

    return { mutate, isPending, error };
}

export function useUpdateBot(groupId: string, botId: string) {
    const [isPending, setIsPending] = useState(false);
    const [error, setError] = useState<Error | null>(null);

    const mutate = useCallback(
        async (updates: UpdateBotInput): Promise<Bot> => {
            setIsPending(true);
            setError(null);
            try {
                const result = await botsApi.updateBot(groupId, botId, updates);
                return result;
            } catch (err) {
                const error =
                    err instanceof Error
                        ? err
                        : new Error("Failed to update bot");
                setError(error);
                throw error;
            } finally {
                setIsPending(false);
            }
        },
        [groupId, botId]
    );

    return { mutate, isPending, error };
}

export function useDeleteBot() {
    const [isPending, setIsPending] = useState(false);
    const [error, setError] = useState<Error | null>(null);

    const mutate = useCallback(
        async (groupId: string, botId: string): Promise<void> => {
            setIsPending(true);
            setError(null);
            try {
                await botsApi.deleteBot(groupId, botId);
            } catch (err) {
                const error =
                    err instanceof Error
                        ? err
                        : new Error("Failed to delete bot");
                setError(error);
                throw error;
            } finally {
                setIsPending(false);
            }
        },
        []
    );

    return { mutate, isPending, error };
}

export function useDuplicateBot() {
    const [isPending, setIsPending] = useState(false);
    const [error, setError] = useState<Error | null>(null);

    const mutate = useCallback(
        async (params: {
            groupId: string;
            botId: string;
            name?: string;
        }): Promise<Bot> => {
            setIsPending(true);
            setError(null);
            try {
                const result = await botsApi.duplicateBot(
                    params.groupId,
                    params.botId,
                    params.name
                );
                return result;
            } catch (err) {
                const error =
                    err instanceof Error
                        ? err
                        : new Error("Failed to duplicate bot");
                setError(error);
                throw error;
            } finally {
                setIsPending(false);
            }
        },
        []
    );

    return { mutate, isPending, error };
}
