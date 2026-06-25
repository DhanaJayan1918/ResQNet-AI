/**
 * ResQNet AI - Incident API Client
 */

import apiClient from './client';
import type {
  CreateIncidentRequest, UpdateIncidentRequest, BulkImportRequest,
  MergeIncidentsRequest, IncidentFilterParams, IncidentSummaryResponse,
  IncidentDetailResponse, PaginatedResponse, TimelineEvent
} from '../types';

export const incidentsApi = {
  submitIncident: async (data: CreateIncidentRequest): Promise<IncidentDetailResponse> => {
    const response = await apiClient.post<IncidentDetailResponse>('/incidents', data);
    return response.data;
  },

  uploadImage: async (file: File): Promise<{ image_url: string }> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post<{ image_url: string }>('/incidents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  getIncidents: async (
    filters: IncidentFilterParams & { page?: number; page_size?: number }
  ): Promise<PaginatedResponse<IncidentSummaryResponse>> => {
    const response = await apiClient.get<PaginatedResponse<IncidentSummaryResponse>>('/incidents', {
      params: filters,
    });
    return response.data;
  },

  getIncidentById: async (id: string): Promise<IncidentDetailResponse> => {
    const response = await apiClient.get<IncidentDetailResponse>(`/incidents/${id}`);
    return response.data;
  },

  updateIncident: async (id: string, data: UpdateIncidentRequest): Promise<IncidentDetailResponse> => {
    const response = await apiClient.patch<IncidentDetailResponse>(`/incidents/${id}`, data);
    return response.data;
  },

  reprocessIncident: async (id: string): Promise<IncidentDetailResponse> => {
    const response = await apiClient.post<IncidentDetailResponse>(`/incidents/${id}/reprocess`);
    return response.data;
  },

  getPriorityQueue: async (page = 1, pageSize = 20): Promise<PaginatedResponse<IncidentSummaryResponse>> => {
    const response = await apiClient.get<PaginatedResponse<IncidentSummaryResponse>>('/incidents/priority-queue', {
      params: { page, page_size: pageSize },
    });
    return response.data;
  },

  bulkImport: async (data: BulkImportRequest): Promise<IncidentDetailResponse[]> => {
    const response = await apiClient.post<IncidentDetailResponse[]>('/incidents/bulk-import', data);
    return response.data;
  },

  getTimeline: async (id: string): Promise<TimelineEvent[]> => {
    const response = await apiClient.get<TimelineEvent[]>(`/incidents/${id}/timeline`);
    return response.data;
  },

  mergeDuplicates: async (id: string, data: MergeIncidentsRequest): Promise<IncidentDetailResponse> => {
    const response = await apiClient.post<IncidentDetailResponse>(`/incidents/${id}/merge`, data);
    return response.data;
  },
};
