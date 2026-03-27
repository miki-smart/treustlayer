import { describe, it, expect, vi, beforeEach } from 'vitest';
import { authApi, kycApi, trustApi, appsApi, auditApi } from '../api';

describe('API Service', () => {
  beforeEach(() => {
    global.fetch = vi.fn();
  });

  describe('authApi', () => {
    it('should call login endpoint', async () => {
      const mockResponse = {
        access_token: 'token',
        user: { id: 'user-123', email: 'test@example.com' },
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await authApi.login('test@example.com', 'password');

      expect(result).toEqual(mockResponse);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/login'),
        expect.objectContaining({
          method: 'POST',
        })
      );
    });

    it('should call register endpoint', async () => {
      const mockUser = { id: 'user-123', email: 'new@example.com' };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockUser,
      });

      const result = await authApi.register({
        email: 'new@example.com',
        username: 'newuser',
        password: 'password',
      });

      expect(result).toEqual(mockUser);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/register'),
        expect.objectContaining({
          method: 'POST',
        })
      );
    });

    it('should call logout endpoint', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ message: 'Logged out' }),
      });

      await authApi.logout();

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/logout'),
        expect.objectContaining({
          method: 'POST',
        })
      );
    });
  });

  describe('kycApi', () => {
    it('should submit KYC with multipart form data', async () => {
      const mockKYC = { id: 'kyc-123', status: 'pending' };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockKYC,
      });

      const formData = new FormData();
      formData.append('id_front', new Blob(['fake']), 'id.jpg');

      const result = await kycApi.submit(formData);

      expect(result).toEqual(mockKYC);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/kyc/submit'),
        expect.objectContaining({
          method: 'POST',
        })
      );
    });

    it('should get KYC status', async () => {
      const mockStatus = { status: 'approved', tier: 'tier_2' };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockStatus,
      });

      const result = await kycApi.status();

      expect(result).toEqual(mockStatus);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/kyc/status'),
        expect.any(Object)
      );
    });

    it('should approve KYC submission', async () => {
      const mockApproved = { id: 'kyc-123', status: 'approved' };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockApproved,
      });

      const result = await kycApi.approve('kyc-123', {
        tier: 'tier_2',
        notes: 'Approved',
      });

      expect(result).toEqual(mockApproved);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/kyc/approve/kyc-123'),
        expect.objectContaining({
          method: 'POST',
        })
      );
    });
  });

  describe('trustApi', () => {
    it('should get user trust profile', async () => {
      const mockProfile = {
        user_id: 'user-123',
        trust_score: 85,
        risk_level: 'low',
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockProfile,
      });

      const result = await trustApi.getUserProfile('user-123');

      expect(result).toEqual(mockProfile);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/trust/profile/user-123'),
        expect.any(Object)
      );
    });

    it('should evaluate trust score', async () => {
      const mockEvaluation = { trust_score: 75, risk_level: 'medium' };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockEvaluation,
      });

      const result = await trustApi.evaluate('user-123');

      expect(result).toEqual(mockEvaluation);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/trust/evaluate'),
        expect.objectContaining({
          method: 'POST',
        })
      );
    });
  });

  describe('appsApi', () => {
    it('should register new app', async () => {
      const mockApp = {
        id: 'app-123',
        name: 'Test App',
        client_id: 'app_abc',
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockApp,
      });

      const result = await appsApi.register({
        name: 'Test App',
        allowed_scopes: ['openid'],
        redirect_uris: ['http://localhost:3000'],
      });

      expect(result).toEqual(mockApp);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/apps'),
        expect.objectContaining({
          method: 'POST',
        })
      );
    });

    it('should list user apps', async () => {
      const mockApps = [{ id: 'app-1', name: 'App 1' }];

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockApps,
      });

      const result = await appsApi.mine();

      expect(result).toEqual(mockApps);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/apps/mine'),
        expect.any(Object)
      );
    });

    it('should approve app', async () => {
      const mockApp = { id: 'app-123', is_approved: true };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockApp,
      });

      const result = await appsApi.approve('app-123');

      expect(result).toEqual(mockApp);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/apps/app-123/approve'),
        expect.objectContaining({
          method: 'POST',
        })
      );
    });
  });

  describe('auditApi', () => {
    it('should list audit entries', async () => {
      const mockEntries = [
        { id: 'audit-1', action: 'user.created' },
        { id: 'audit-2', action: 'kyc.approved' },
      ];

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockEntries,
      });

      const result = await auditApi.list();

      expect(result).toEqual(mockEntries);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/audit/entries'),
        expect.any(Object)
      );
    });

    it('should list audit entries with filters', async () => {
      const mockEntries = [{ id: 'audit-1', action: 'user.created' }];

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockEntries,
      });

      const result = await auditApi.list({
        action: 'user.created',
        resource_type: 'user',
      });

      expect(result).toEqual(mockEntries);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('action=user.created'),
        expect.any(Object)
      );
    });
  });

  describe('Error Handling', () => {
    it('should throw error on 401 Unauthorized', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Unauthorized' }),
      });

      await expect(authApi.login('test@example.com', 'wrong')).rejects.toThrow();
    });

    it('should throw error on 403 Forbidden', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 403,
        json: async () => ({ detail: 'Forbidden' }),
      });

      await expect(kycApi.approve('kyc-123', { tier: 'tier_2' })).rejects.toThrow();
    });

    it('should throw error on 404 Not Found', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
        json: async () => ({ detail: 'Not found' }),
      });

      await expect(trustApi.getUserProfile('non-existent')).rejects.toThrow();
    });

    it('should throw error on 500 Server Error', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        json: async () => ({ detail: 'Internal server error' }),
      });

      await expect(appsApi.list()).rejects.toThrow();
    });
  });
});
