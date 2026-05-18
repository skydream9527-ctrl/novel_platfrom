import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { agentApi, scheduledApi, skillApi, taskApi, templateApi } from "@/api/endpoints";
import type { ApiError } from "@/api/client";
import type { AgentCard, SkillCard } from "@/types/api";
import type { TemplateRecord } from "@/api/endpoints";
import { TopNav } from "@/components/shell/TopNav";
import { useUIStore } from "@/stores/uiStore";
import "./CreateTask.css";

type Step = 1 | 2 | 3;

const PARADIGM_PLACEHOLDER: Record<string, string> = {
  biz: "上周新版本上线后的留存表现 / 经营异常拆解…",
  ab: "v2.3 vs v2.2 留存对比，样本均衡 + 显著性…",
  wave: "周末 GMV 突然下滑，多维下钻定位根因…",
  data: "本月各渠道 ARPU + 同比环比，自动可视化…",
  gray: "v1.5 vs v1.4 灰度版本的核心指标差异…",
  open: "任意目标：跨范式协作 / 多工具编排 / 自由探索…",
};

const PARADIGM_NAME: Record<string, string> = {
  biz: "经营分析",
  ab: "AB 实验",
  wave: "波动分析",
  data: "数据分析",
  gray: "版本灰度",
  open: "开放任务",
};

export function CreateTaskPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const pushToast = useUIStore((s) => s.pushToast);

  const initialOrigin = (() => {
    const o = params.get("origin");
    return o === "open" || o === "template" || o === "public" ? o : "blank";
  })();

  const [step, setStep] = useState<Step>(1);
  const [origin, setOrigin] = useState<"blank" | "open" | "template" | "public">(initialOrigin);
  const [agents, setAgents] = useState<AgentCard[]>([]);
  const [skills, setSkills] = useState<SkillCard[]>([]);
  const [myTemplates, setMyTemplates] = useState<TemplateRecord[]>([]);
  const [pubTemplates, setPubTemplates] = useState<TemplateRecord[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<TemplateRecord | null>(null);

  const [form, setForm] = useState({
    name: "",
    paradigm: params.get("paradigm") || "biz",
    description: "",
    agent_id: params.get("agentId") || "",
    skill_ids: [] as string[],
    initial_prompt: "",
    visibility: "private",
    enable_schedule: false,
    cron: "0 9 * * *",
    schedule_prompt: "",
    auto_open: true,
  });
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    agentApi.list().then((r) => setAgents(r.items)).catch(() => {});
    skillApi.list().then((r) => setSkills(r.items)).catch(() => {});
    templateApi.list("private").then((r) => setMyTemplates(r.items)).catch(() => {});
    templateApi.list("public").then((r) => setPubTemplates(r.items)).catch(() => {});
  }, []);

  useEffect(() => {
    const tplId = params.get("template");
    if (tplId) {
      templateApi.get(tplId).then((t) => applyTemplate(t)).catch(() => {});
    }
  }, [params]);

  const filteredAgents = useMemo(
    () => agents.filter((a) => !form.paradigm || a.paradigm === form.paradigm),
    [agents, form.paradigm],
  );

  const applyTemplate = (t: TemplateRecord) => {
    setSelectedTemplate(t);
    setForm((f) => ({
      ...f,
      paradigm: t.paradigm,
      agent_id: t.agent_id || "",
      skill_ids: t.skill_ids,
      initial_prompt: t.initial_prompt || "",
      enable_schedule: t.has_schedule,
      cron: (t.schedule_config as any)?.cron || "0 9 * * *",
      schedule_prompt: (t.schedule_config as any)?.prompt || "",
      name: f.name || t.name,
    }));
    setOrigin("template");
  };

  const submit = async () => {
    if (!form.name.trim()) {
      pushToast("warning", "请填写任务名称");
      setStep(2);
      return;
    }
    setCreating(true);
    try {
      const t = await taskApi.create({
        name: form.name.trim(),
        paradigm: form.paradigm,
        agent_id: form.agent_id || null,
        description: form.description || undefined,
        initial_prompt: form.initial_prompt || undefined,
        skill_ids: form.skill_ids,
        visibility: form.visibility,
      });
      if (form.enable_schedule) {
        try {
          await scheduledApi.create(t.id, {
            name: `${form.name} · 定时`,
            cron: form.cron,
            prompt: form.schedule_prompt || form.initial_prompt || "",
          });
        } catch (err) {
          pushToast("warning", `定时配置失败：${(err as Error).message}`);
        }
      }
      pushToast("success", "任务已创建");
      if (form.auto_open) navigate(`/workspace/${t.id}`);
      else navigate("/dashboard");
    } catch (err) {
      const e = err as ApiError;
      pushToast("error", `创建失败：${e.message}`);
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="ct-page">
      <TopNav mode="workspace" crumb={<span>首页 / <span className="current">创建任务</span></span>} />

      <main className="ct-main">
        <div className="ct-stepper">
          {[1, 2, 3].map((n) => (
            <div key={n} className={`ct-step ${step === n ? "active" : ""} ${step > n ? "done" : ""}`}>
              <div className="ct-step-num">{step > n ? "✓" : n}</div>
              <div className="ct-step-label">
                {n === 1 ? "选择起点" : n === 2 ? "任务基础" : "高级配置"}
              </div>
            </div>
          ))}
        </div>

        {step === 1 && (
          <section className="ct-section">
            <div className="ct-origin-grid">
              <button
                className={`ct-origin ${origin === "blank" ? "selected" : ""}`}
                onClick={() => {
                  setOrigin("blank");
                  setSelectedTemplate(null);
                }}
              >
                <div className="co-icon">📝</div>
                <div className="co-name">空白任务</div>
                <div className="co-desc">从 0 开始，自由配置</div>
              </button>
              <button
                className={`ct-origin ${origin === "open" ? "selected" : ""}`}
                onClick={() => {
                  setOrigin("open");
                  setSelectedTemplate(null);
                  setForm((f) => ({
                    ...f,
                    paradigm: "open",
                    agent_id: "general",
                  }));
                }}
              >
                <div className="co-icon">🤖</div>
                <div className="co-name">开放任务</div>
                <div className="co-desc">通用 Agent，跨范式自由对话</div>
              </button>
              <button
                className={`ct-origin ${origin === "template" ? "selected" : ""}`}
                onClick={() => setOrigin("template")}
              >
                <div className="co-icon">📋</div>
                <div className="co-name">从模板</div>
                <div className="co-desc">复用我的或公共模板</div>
              </button>
              <button
                className={`ct-origin ${origin === "public" ? "selected" : ""}`}
                onClick={() => setOrigin("public")}
              >
                <div className="co-icon">🌐</div>
                <div className="co-name">公共任务</div>
                <div className="co-desc">参考团队已有任务</div>
              </button>
            </div>

            {origin === "template" && (
              <div className="ct-template-panel">
                <div className="ct-tpl-tabs">
                  <span>📌 我的模板（{myTemplates.length}）</span>
                  <span>🌐 公共模板（{pubTemplates.length}）</span>
                </div>
                <div className="ct-tpl-grid">
                  {[...myTemplates, ...pubTemplates].map((t) => (
                    <button
                      key={t.id}
                      className={`ct-tpl-card ${selectedTemplate?.id === t.id ? "selected" : ""}`}
                      onClick={() => applyTemplate(t)}
                    >
                      <div className="ct-tpl-name">{t.name}</div>
                      <div className="ct-tpl-meta">
                        {PARADIGM_NAME[t.paradigm] || t.paradigm} ·{" "}
                        {t.visibility === "public" ? "公共" : "私有"}
                      </div>
                      {t.description && <div className="ct-tpl-desc">{t.description}</div>}
                    </button>
                  ))}
                  {myTemplates.length + pubTemplates.length === 0 && (
                    <div className="ct-empty">暂无可用模板</div>
                  )}
                </div>
              </div>
            )}

            <div className="ct-actions">
              <button className="btn-primary" onClick={() => setStep(2)}>
                下一步 →
              </button>
            </div>
          </section>
        )}

        {step === 2 && (
          <section className="ct-section">
            <div className="ct-fields">
              <label className="ct-field">
                <span>任务名称</span>
                <input
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="例如：Q2 经营复盘 · 渠道归因"
                />
              </label>
              <label className="ct-field">
                <span>范式</span>
                <select
                  value={form.paradigm}
                  onChange={(e) => setForm({ ...form, paradigm: e.target.value })}
                >
                  {Object.entries(PARADIGM_NAME).map(([k, v]) => (
                    <option key={k} value={k}>
                      {v}
                    </option>
                  ))}
                </select>
              </label>
              <label className="ct-field full">
                <span>描述（可选）</span>
                <input
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  placeholder="一句话描述任务目标"
                />
              </label>
              <label className="ct-field full">
                <span>💬 初始 Prompt</span>
                <textarea
                  rows={4}
                  value={form.initial_prompt}
                  onChange={(e) => setForm({ ...form, initial_prompt: e.target.value })}
                  placeholder={PARADIGM_PLACEHOLDER[form.paradigm] || "Agent 初始指令…"}
                />
              </label>
            </div>
            <div className="ct-actions">
              <button className="btn-secondary" onClick={() => setStep(1)}>← 上一步</button>
              <button className="btn-primary" onClick={() => setStep(3)}>下一步 →</button>
            </div>
          </section>
        )}

        {step === 3 && (
          <section className="ct-section">
            <details className="ct-fold" open>
              <summary>🤖 Agent 与 Skills</summary>
              <div className="ct-fold-body">
                <label className="ct-field">
                  <span>Agent</span>
                  <select
                    value={form.agent_id}
                    onChange={(e) => setForm({ ...form, agent_id: e.target.value })}
                  >
                    <option value="">系统自动选择</option>
                    {filteredAgents.map((a) => (
                      <option key={a.id} value={a.id}>
                        {a.icon} {a.name}
                      </option>
                    ))}
                  </select>
                </label>
                <div className="ct-skills">
                  <div className="ct-skill-head">绑定 Skills（共 {skills.length} 个）</div>
                  <div className="ct-skill-list">
                    {skills.map((s) => {
                      const checked = form.skill_ids.includes(s.id);
                      return (
                        <label key={s.id} className={`ct-skill ${checked ? "on" : ""}`}>
                          <input
                            type="checkbox"
                            checked={checked}
                            onChange={(e) =>
                              setForm({
                                ...form,
                                skill_ids: e.target.checked
                                  ? [...form.skill_ids, s.id]
                                  : form.skill_ids.filter((x) => x !== s.id),
                              })
                            }
                          />
                          <span className="ct-skill-name">{s.name}</span>
                          <span className="ct-skill-desc">{s.description}</span>
                        </label>
                      );
                    })}
                  </div>
                </div>
              </div>
            </details>

            <details className="ct-fold">
              <summary>⏱ 定时执行</summary>
              <div className="ct-fold-body">
                <label className="ct-toggle">
                  <input
                    type="checkbox"
                    checked={form.enable_schedule}
                    onChange={(e) => setForm({ ...form, enable_schedule: e.target.checked })}
                  />
                  启用定时执行
                </label>
                {form.enable_schedule && (
                  <>
                    <label className="ct-field">
                      <span>cron 表达式</span>
                      <input
                        value={form.cron}
                        onChange={(e) => setForm({ ...form, cron: e.target.value })}
                        placeholder="例如 0 9 * * 1-5（工作日早 9 点）"
                      />
                      <small style={{ color: "var(--text-muted)" }}>{cronHint(form.cron)}</small>
                    </label>
                    <div className="ct-cron-presets">
                      {[
                        { label: "每天 09:00", v: "0 9 * * *" },
                        { label: "工作日 09:00", v: "0 9 * * 1-5" },
                        { label: "每周一 09:00", v: "0 9 * * 1" },
                        { label: "每小时", v: "0 * * * *" },
                      ].map((p) => (
                        <button
                          key={p.v}
                          className="btn-ghost"
                          onClick={() => setForm({ ...form, cron: p.v })}
                        >
                          {p.label}
                        </button>
                      ))}
                    </div>
                    <label className="ct-field">
                      <span>定时 Prompt</span>
                      <textarea
                        rows={3}
                        value={form.schedule_prompt}
                        onChange={(e) =>
                          setForm({ ...form, schedule_prompt: e.target.value })
                        }
                        placeholder="留空则使用初始 Prompt"
                      />
                    </label>
                  </>
                )}
              </div>
            </details>

            <details className="ct-fold">
              <summary>🌐 可见性</summary>
              <div className="ct-fold-body">
                <div className="ct-visibility">
                  <label>
                    <input
                      type="radio"
                      checked={form.visibility === "private"}
                      onChange={() => setForm({ ...form, visibility: "private" })}
                    />
                    私有 · 仅我可见
                  </label>
                  <label>
                    <input
                      type="radio"
                      checked={form.visibility === "public"}
                      onChange={() => setForm({ ...form, visibility: "public" })}
                    />
                    公共 · 团队可见（需 admin 审核）
                  </label>
                </div>
              </div>
            </details>

            <div className="ct-confirm">
              <label className="ct-toggle">
                <input
                  type="checkbox"
                  checked={form.auto_open}
                  onChange={(e) => setForm({ ...form, auto_open: e.target.checked })}
                />
                创建后立即打开 Workspace
              </label>
            </div>

            <div className="ct-actions">
              <button className="btn-secondary" onClick={() => setStep(2)}>← 上一步</button>
              <button className="btn-primary" disabled={creating} onClick={submit}>
                {creating ? "创建中…" : "创建任务"}
              </button>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

function cronHint(expr: string): string {
  const p = expr.trim().split(/\s+/);
  if (p.length !== 5) return "请输入 5 段 cron 表达式";
  const [m, h, dom, mo, dow] = p;
  return `分=${m} 时=${h} 日=${dom} 月=${mo} 周=${dow}`;
}
