import client from "./client";

export interface GraphNode {
  id: string;
  type: "chapter" | "character" | "note" | "source" | "tag";
  label: string;
  data: Record<string, any>;
  position?: { x: number; y: number };
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: "reference" | "appearance" | "tag" | "belongs_to" | "relation";
  label?: string;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
  stats: {
    total_nodes: number;
    total_edges: number;
    chapters: number;
    characters: number;
    notes: number;
    sources: number;
    tags: number;
  };
}

export interface NeighborData {
  center: GraphNode;
  neighbors: GraphNode[];
  edges: GraphEdge[];
}

export interface PathData {
  found: boolean;
  path: GraphNode[];
  edges: GraphEdge[];
  length: number;
}

export async function getGraph(taskId: number, type?: string): Promise<GraphData> {
  const response = await client.get(`/graph/by-task/${taskId}`, {
    params: { type },
  });
  return response.data;
}

export async function getNeighbors(
  nodeType: string,
  nodeId: number,
  taskId: number,
  depth: number = 1
): Promise<NeighborData> {
  const response = await client.get(`/graph/neighbors/${nodeType}/${nodeId}`, {
    params: { task_id: taskId, depth },
  });
  return response.data;
}

export async function findPath(
  fromType: string,
  fromId: number,
  toType: string,
  toId: number,
  taskId: number
): Promise<PathData> {
  const response = await client.get(
    `/graph/path/${fromType}/${fromId}/${toType}/${toId}`,
    { params: { task_id: taskId } }
  );
  return response.data;
}
