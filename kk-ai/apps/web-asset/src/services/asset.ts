export interface Asset {
  id: string;
  name: string;
  description?: string;
  asset_type: string;
  category?: string;
  tags?: string[];
  status: string;
  download_count: number;
  reuse_count: number;
  created_at: string;
  updated_at: string;
}

export interface AssetSearchResponse {
  data: Asset[];
  total: number;
  page: number;
  page_size: number;
}

export interface AssetStats {
  total_count: number;
  by_type: Record<string, number>;
  by_status: Record<string, number>;
  by_category: Record<string, number>;
  reuse_rate: number;
  total_downloads: number;
}

const BASE = "/v1/assets";

export async function fetchAssets(params: {
  q?: string;
  asset_type?: string;
  tags?: string[];
  page?: number;
  page_size?: number;
}): Promise<AssetSearchResponse> {
  const sp = new URLSearchParams();
  if (params.q) sp.set("q", params.q);
  if (params.asset_type) sp.set("asset_type", params.asset_type);
  if (params.tags) params.tags.forEach((t) => sp.append("tags", t));
  sp.set("page", String(params.page || 1));
  sp.set("page_size", String(params.page_size || 20));
  const res = await fetch(`${BASE}/search?${sp.toString()}`);
  if (!res.ok) throw new Error("搜索素材失败");
  return res.json();
}

export async function fetchAsset(id: string): Promise<Asset> {
  const res = await fetch(`${BASE}/${id}`);
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

export async function generatePoster(
  assetId: string,
  variables: Record<string, string>,
): Promise<{ url: string }> {
  const res = await fetch(`${BASE}/${assetId}/generate_poster`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ variables }),
  });
  if (!res.ok) throw new Error("生成海报失败");
  return res.json();
}
