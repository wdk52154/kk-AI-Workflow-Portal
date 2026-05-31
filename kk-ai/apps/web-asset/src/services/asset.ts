export interface Asset {
  id: number;
  asset_id: string;
  name: string;
  description?: string;
  asset_type: string;
  category?: string;
  tags?: string[];
  status: string;
  usage_count: number;
  created_at: string;
  updated_at: string;
}

export interface AssetSearchResponse {
  items: Asset[];
  total: number;
  page: number;
  page_size: number;
}

export interface AssetStats {
  total_assets: number;
  total_by_type: Record<string, number>;
  total_by_status: Record<string, number>;
  top_reused: any[];
  recent_uploads: number;
  reuse_rate: number;
  avg_reuse_multiplier: number;
  approved_count: number;
  reused_count: number;
  total_usages: number;
}

const BASE = "/v1/assets";

export async function fetchAssets(params: {
  q?: string;
  asset_type?: string;
  tags?: string[];
  status?: string;
  page?: number;
  page_size?: number;
}): Promise<AssetSearchResponse> {
  const sp = new URLSearchParams();
  if (params.q) sp.set("q", params.q);
  if (params.asset_type) sp.set("asset_type", params.asset_type);
  if (params.status) sp.set("status", params.status);
  if (params.tags) params.tags.forEach((t) => sp.append("tags", t));
  sp.set("page", String(params.page || 1));
  sp.set("page_size", String(params.page_size || 20));
  const res = await fetch(`${BASE}/search?${sp.toString()}`);
  if (!res.ok) throw new Error("搜索素材失败");
  return res.json();
}

export async function fetchAsset(assetId: string): Promise<Asset> {
  const res = await fetch(`${BASE}/${assetId}`);
  if (!res.ok) throw new Error("获取素材失败");
  return res.json();
}

export async function fetchAssetStats(): Promise<AssetStats> {
  const res = await fetch(`${BASE}/stats`);
  if (!res.ok) throw new Error("获取统计失败");
  return res.json();
}

export async function createAsset(data: FormData): Promise<Asset> {
  const res = await fetch(BASE, {
    method: "POST",
    body: data,
  });
  if (!res.ok) throw new Error("创建素材失败");
  return res.json();
}

export async function updateAssetStatus(
  assetId: string,
  status: string,
): Promise<Asset> {
  const fd = new FormData();
  fd.append("status", status);
  const res = await fetch(`${BASE}/${assetId}/status`, {
    method: "POST",
    body: fd,
  });
  if (!res.ok) throw new Error("更新状态失败");
  return res.json();
}

export async function precheckAsset(assetId: string): Promise<Asset> {
  const res = await fetch(`${BASE}/${assetId}/precheck`, { method: "POST" });
  if (!res.ok) throw new Error("预检失败");
  return res.json();
}

export async function approveAsset(assetId: string): Promise<Asset> {
  const res = await fetch(`${BASE}/${assetId}/approve`, { method: "POST" });
  if (!res.ok) throw new Error("审核通过失败");
  return res.json();
}

export async function rejectAsset(assetId: string): Promise<Asset> {
  const res = await fetch(`${BASE}/${assetId}/reject`, { method: "POST" });
  if (!res.ok) throw new Error("审核拒绝失败");
  return res.json();
}

export async function generatePoster(
  assetId: string,
  variables: Record<string, string>,
): Promise<{ asset_id: string; download_url: string; message: string }> {
  const res = await fetch(`${BASE}/${assetId}/generate_poster`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ variables }),
  });
  if (!res.ok) throw new Error("生成海报失败");
  return res.json();
}
