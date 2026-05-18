import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { agentApi } from "@/api/endpoints";
import type { AgentCard } from "@/types/api";
import { useUIStore } from "@/stores/uiStore";
import "./Introduce.css";

const PARADIGM_DESC: Record<string, string> = {
  biz: "经营数据拆解归因与趋势洞察",
  ab: "AB 实验显著性检验、样本均衡、效应量评估",
  wave: "多维下钻指标异常根因定位",
  data: "自然语言生成 SQL 查询，自动可视化",
  gray: "灰度版本对比与放量决策建议",
};

export function IntroducePage() {
  const [agents, setAgents] = useState<AgentCard[]>([]);
  const toggleTheme = useUIStore((s) => s.toggleTheme);
  const theme = useUIStore((s) => s.theme);

  useEffect(() => {
    agentApi.list().then((r) => setAgents(r.items)).catch(() => {});
  }, []);

  return (
    <div className="intro-page">
      <div className="intro-bg-grid" />
      <div className="intro-orb intro-orb-1" />
      <div className="intro-orb intro-orb-2" />

      <nav className="intro-nav">
        <Link to="/" className="brand">
          <div className="brand-logo">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="#fff" strokeWidth="2">
              <path d="M12 2L2 7l10 5 10-5-10-5z" />
              <path d="M2 17l10 5 10-5" />
              <path d="M2 12l10 5 10-5" />
            </svg>
          </div>
          <span className="brand-name">
            <span className="brand-accent">ICE</span> Data Workbench
          </span>
        </Link>
        <div className="intro-nav-links">
          <a href="#concepts">核心概念</a>
          <a href="#cases">实际案例</a>
          <a href="#features">功能特性</a>
        </div>
        <div className="intro-nav-actions">
          <button className="icon-btn" onClick={toggleTheme}>
            {theme === "dark" ? "🌓" : "☀"}
          </button>
          <Link to="/login" className="cta-nav">
            立即体验 →
          </Link>
        </div>
      </nav>

      <main className="intro-container">
        <section className="intro-hero">
          <span className="intro-tag">AI 数据工作流</span>
          <h1>
            用 <span className="intro-accent">对话</span> 完成
            <br />
            所有数据任务
          </h1>
          <p>
            通过 Agent + 对话驱动，帮助产品团队高效完成数据分析、实验评估、经营洞察等任务。Agent 在每次对话中持续进化。
          </p>
          <div className="intro-cta-row">
            <Link to="/login" className="btn-primary intro-cta">
              立即体验 →
            </Link>
            <Link to="/guide" className="btn-secondary intro-cta">
              查看使用指南
            </Link>
          </div>
          <div className="intro-stats">
            <div>
              <div className="num">{agents.length || 5}</div>
              <div className="label">智能 Agent</div>
            </div>
            <div>
              <div className="num">3</div>
              <div className="label">本地 Skills</div>
            </div>
            <div>
              <div className="num">5</div>
              <div className="label">工作范式</div>
            </div>
            <div>
              <div className="num">2</div>
              <div className="label">登录方式</div>
            </div>
          </div>
        </section>

        <section className="intro-section" id="concepts">
          <h2>核心概念</h2>
          <div className="intro-concept-grid">
            <Concept icon="📋" name="任务" desc="一次完整的数据工作流，独立工作空间，记录对话与产出" />
            <Concept icon="🤖" name="Agent" desc="公共智能体，与范式 1:1 绑定，越用越聪明" />
            <Concept icon="⚡" name="Skill" desc="可执行工具，Agent 通过 function calling 调用" />
            <Concept icon="✨" name="经验卡片" desc="对话中提炼的规则，审批后注入 Agent 上下文" />
            <Concept icon="🎯" name="工作范式" desc="5 种范式预绑定 Agent + Skills + Prompt" />
            <Concept icon="🌐" name="公共区" desc="团队共享的 Agents、Skills、文件、模板" />
          </div>
        </section>

        <section className="intro-section" id="cases">
          <h2>实际案例</h2>
          <div className="intro-case-grid">
            {agents.slice(0, 4).map((a) => (
              <Link key={a.id} to="/login" className="intro-case-card">
                <div className="intro-case-icon">{a.icon}</div>
                <div className="intro-case-name">{a.name}</div>
                <div className="intro-case-desc">{a.description || PARADIGM_DESC[a.paradigm]}</div>
                <span className="intro-case-cta">用此 Agent 创建 →</span>
              </Link>
            ))}
            {agents.length === 0 &&
              Object.entries(PARADIGM_DESC)
                .slice(0, 4)
                .map(([k, v]) => (
                  <Link key={k} to="/login" className="intro-case-card">
                    <div className="intro-case-name">{k}</div>
                    <div className="intro-case-desc">{v}</div>
                  </Link>
                ))}
          </div>
        </section>

        <section className="intro-section" id="features">
          <h2>覆盖完整功能</h2>
          <div className="intro-feat-grid">
            <Feature n="01" title="认证与三级角色" desc="飞书 OAuth + JWT 双 token + super/admin/user" />
            <Feature n="02" title="Workspace 三栏" desc="文件 + 流式对话 + Tool Calling + 文件预览" />
            <Feature n="03" title="Agent 进化" desc="Prompt 版本历史 + 测试沙盒 + 经验卡片" />
            <Feature n="04" title="文件优先存储" desc="文件系统是 source of truth，SQLite 仅 cache" />
            <Feature n="05" title="定时任务" desc="cron + Agent 自动执行 + 推送" />
            <Feature n="06" title="管理后台" desc="用户 / Agent / Skill / KB / 审计 / 用量" />
          </div>
        </section>
      </main>

      <footer className="intro-footer">ICE Data Workbench v3 · 2026-05-07</footer>
    </div>
  );
}

function Concept({ icon, name, desc }: { icon: string; name: string; desc: string }) {
  return (
    <div className="intro-concept">
      <div className="intro-concept-icon">{icon}</div>
      <div className="intro-concept-name">{name}</div>
      <div className="intro-concept-desc">{desc}</div>
    </div>
  );
}

function Feature({ n, title, desc }: { n: string; title: string; desc: string }) {
  return (
    <div className="intro-feat">
      <div className="intro-feat-num">{n}</div>
      <div>
        <div className="intro-feat-title">{title}</div>
        <div className="intro-feat-desc">{desc}</div>
      </div>
    </div>
  );
}
