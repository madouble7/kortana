import { beforeEach, describe, expect, it, jest } from '@jest/globals';
import fs from 'node:fs';
import { AuthorizationService } from '../AuthorizationService.ts';
import { DeploymentError, DeploymentService } from '../DeploymentService.ts';
import { GovernanceService } from '../GovernanceService.ts';

jest.mock('node:fs');

describe('DeploymentService', () => {
    const MOCK_TASK_ID = 'task-deploy-123';
    const MOCK_STAGING_DIR = 'staging-abc';

    beforeEach(() => {
        jest.restoreAllMocks();
        jest.spyOn(console, 'log').mockImplementation(() => { });
        jest.spyOn(console, 'error').mockImplementation(() => { });
    });

    it('throws an error if task is not authorized', async () => {
        jest.spyOn(AuthorizationService, 'isTaskAuthorized').mockReturnValue(false);

        await expect(DeploymentService.deploy(MOCK_TASK_ID, MOCK_STAGING_DIR))
            .rejects.toThrow(`Task ${MOCK_TASK_ID} is not authorized for deployment.`);
    });

    it('throws an error if staging directory does not exist', async () => {
        jest.spyOn(AuthorizationService, 'isTaskAuthorized').mockReturnValue(true);
        // Mock fs.existsSync using spyOn instead of the global jest.mock
        jest.spyOn(fs, 'existsSync').mockReturnValue(false);

        await expect(DeploymentService.deploy(MOCK_TASK_ID, MOCK_STAGING_DIR))
            .rejects.toThrow(/Staging directory .* does not exist\./);
    });

    it('returns manifest and skips fs.renameSync on dryRun', async () => {
        jest.spyOn(AuthorizationService, 'isTaskAuthorized').mockReturnValue(true);
        jest.spyOn(fs, 'existsSync').mockReturnValue(true);
        jest.spyOn(fs, 'readdirSync').mockReturnValue(['file1.ts' as any, 'file2.ts' as any]);
        const renameSpy = jest.spyOn(fs, 'renameSync').mockImplementation(() => { });

        // Call with dryRun: true
        const manifest = await DeploymentService.deploy(MOCK_TASK_ID, MOCK_STAGING_DIR, { dryRun: true });

        expect(renameSpy).not.toHaveBeenCalled();
        expect(manifest.dryRun).toBe(true);
        expect(manifest.files).toEqual(['file1.ts', 'file2.ts']);
        expect(manifest.status).toBe('success');
    });

    it('moves files from staging to core, returns manifest, and logs audit event', async () => {
        jest.spyOn(AuthorizationService, 'isTaskAuthorized').mockReturnValue(true);

        // Setup file system mocks
        jest.spyOn(fs, 'existsSync').mockReturnValue(true);
        jest.spyOn(fs, 'readdirSync').mockReturnValue(['file1.ts' as any, 'file2.ts' as any]);
        const renameSpy = jest.spyOn(fs, 'renameSync').mockImplementation(() => { });

        const auditSpy = jest.spyOn(GovernanceService, 'logAuditEvent').mockImplementation(() => { });

        const manifest = await DeploymentService.deploy(MOCK_TASK_ID, MOCK_STAGING_DIR);

        expect(AuthorizationService.isTaskAuthorized).toHaveBeenCalledWith(MOCK_TASK_ID);

        // Should iterate over the 2 files
        expect(fs.readdirSync).toHaveBeenCalled();
        expect(renameSpy).toHaveBeenCalledTimes(2);

        expect(manifest.dryRun).toBe(false);
        expect(manifest.status).toBe('success');
        expect(manifest.files).toEqual(['file1.ts', 'file2.ts']);

        expect(auditSpy).toHaveBeenCalledWith(
            MOCK_TASK_ID,
            'CORE_DEPLOYMENT',
            expect.objectContaining({ stagingSubDir: MOCK_STAGING_DIR })
        );
    });

    it('rolls back successfully moved files if a partial failure occurs and returns manifest in error', async () => {
        jest.spyOn(AuthorizationService, 'isTaskAuthorized').mockReturnValue(true);
        jest.spyOn(fs, 'existsSync').mockReturnValue(true);
        jest.spyOn(fs, 'readdirSync').mockReturnValue(['file1.ts' as any, 'fail.ts' as any]);

        const renameSpy = jest.spyOn(fs, 'renameSync').mockImplementation((src, dest) => {
            if (typeof src === 'string' && src.includes('fail.ts')) {
                throw new Error('Disk IO Error on fail.ts');
            }
        });

        let caughtError: DeploymentError | null = null;
        try {
            await DeploymentService.deploy(MOCK_TASK_ID, MOCK_STAGING_DIR);
        } catch (e: any) {
            caughtError = e;
        }

        expect(caughtError).not.toBeNull();
        expect(caughtError?.message).toContain('Rolled back successfully');
        expect(caughtError?.manifest).toBeDefined();
        expect(caughtError?.manifest?.status).toBe('rolled_back');
        expect(caughtError?.manifest?.files).toEqual(['file1.ts', 'fail.ts']);

        // Order of calls:
        // 1. file1.ts forward
        // 2. fail.ts forward (throws)
        // 3. file1.ts backward (rollback)
        expect(renameSpy).toHaveBeenCalledTimes(3);

        const firstCall = renameSpy.mock.calls[0];
        const rollbackCall = renameSpy.mock.calls[2];

        const file1Src = firstCall[0] as string;
        const file1Dest = firstCall[1] as string;

        // Rollback call should reverse the parameters of the first call
        expect(rollbackCall[0]).toBe(file1Dest);
        expect(rollbackCall[1]).toBe(file1Src);
    });
});
