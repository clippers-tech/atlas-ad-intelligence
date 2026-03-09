import { useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";

interface ImportResult {
  updated: number;
  created: number;
  errors: string[];
}

export function useLeadImport() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (formData: FormData): Promise<ImportResult> => {
      const res = await api.post<ImportResult>("/leads/import", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["leads"] });
    },
  });
}
