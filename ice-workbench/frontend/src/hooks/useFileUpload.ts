import { useCallback, useState } from "react";
import { fileApi, sysApi } from "@/api/endpoints";
import { useUIStore } from "@/stores/uiStore";
import type { ApiError } from "@/api/client";
import type { FileMeta } from "@/types/api";

interface UploadProgress {
  name: string;
  percent: number;
  status: "pending" | "uploading" | "done" | "error";
  message?: string;
}

interface UseFileUploadOpts {
  taskId: string;
  scope?: "uploaded" | "input" | "output";
  onSuccess?: (file: FileMeta) => void;
}

const HARD_CAP_DEFAULT_MB = 50;
const MAX_DEFAULT_MB = 20;

export function useFileUpload(opts: UseFileUploadOpts) {
  const [items, setItems] = useState<UploadProgress[]>([]);
  const pushToast = useUIStore((s) => s.pushToast);

  const upload = useCallback(
    async (files: FileList | File[]) => {
      const list = Array.from(files);
      let cap = HARD_CAP_DEFAULT_MB;
      let warn = MAX_DEFAULT_MB;
      try {
        const t = await sysApi.toggles();
        cap = t.upload_max_size_hard_cap_mb;
        warn = t.upload_max_size_mb;
      } catch {
        /* fallback */
      }
      for (const f of list) {
        if (f.size > cap * 1024 * 1024) {
          pushToast("error", `文件 ${f.name} 超过 ${cap}MB 上限，无法上传`);
          continue;
        }
        if (f.size > warn * 1024 * 1024) {
          pushToast("warning", `文件 ${f.name} 较大（${(f.size / 1024 / 1024).toFixed(1)}MB），上传可能较慢`);
        }
        const idx = items.length;
        setItems((arr) => [...arr, { name: f.name, percent: 0, status: "uploading" }]);
        try {
          const meta = await fileApi.upload(opts.taskId, f, opts.scope || "uploaded");
          setItems((arr) =>
            arr.map((it, i) => (i === idx ? { ...it, percent: 100, status: "done" } : it)),
          );
          opts.onSuccess?.(meta);
          pushToast("success", `${meta.name} 上传成功`);
        } catch (err) {
          const e = err as ApiError;
          setItems((arr) =>
            arr.map((it, i) =>
              i === idx ? { ...it, status: "error", message: e.message } : it,
            ),
          );
          pushToast("error", `${f.name} 上传失败：${e.message || "未知错误"}`);
        }
      }
    },
    [opts, items.length, pushToast],
  );

  return { items, upload, clear: () => setItems([]) };
}
