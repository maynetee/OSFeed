import { api as client } from './client';
import { IntelligenceDashboard, ClusterDetail } from '../../types/intelligence';

export const intelligenceApi = {
  getDashboard: async () => {
    const response = await client.get<IntelligenceDashboard>('/api/intelligence/dashboard');
    return response.data;
  },

  getClusterDetail: async (clusterId: string) => {
    const response = await client.get<ClusterDetail>(`/api/intelligence/clusters/${clusterId}`);
    return response.data;
  }
};
