import { beforeEach, describe, expect, it, jest } from '@jest/globals';
import util from 'node:util';
import type { Task } from '../../../src/types.ts';

const mockPromisifiedExec = jest.fn().mockResolvedValue({ stdout: 'mock stdout', stderr: '' } as any);

const mockExec = Object.assign(
    jest.fn((cmd: string, options: any, callback: Function) => {
        callback(null, 'mock stdout', '');
    }),
    {
        [util.promisify.custom]: mockPromisifiedExec
    }
);

jest.unstable_mockModule('node:child_process', () => ({
    exec: mockExec
}));

// Use dynamic import so the mock applies before TestRunnerService evaluates child_process
const { TestRunnerService } = await import('../TestRunnerService.ts');

const createBaseTask = (): Task => ({
    id: "test-task-1",
    status: "coded",
    description: "Test the runner",
    priority: "normal",
    created_at: new Date().toISOString(),
});

describe('TestRunnerService', () => {
    beforeEach(() => {
        mockExec.mockClear();
        mockPromisifiedExec.mockClear();
    });

    it('runs the default lint command when no tests are specified', async () => {
        mockPromisifiedExec.mockResolvedValueOnce({ stdout: 'lint passed', stderr: '' } as any);

        const task = createBaseTask();
        const result = await TestRunnerService.runTests(task);

        expect(result.ok).toBe(true);
        expect(result.artifacts?.command).toBe('npm run lint');
        expect(result.artifacts?.exit_code).toBe(0);
        expect(result.artifacts?.stdout).toBe('lint passed');
    });

    it('allows safe command from plan', async () => {
        mockPromisifiedExec.mockResolvedValueOnce({ stdout: 'tests passed', stderr: '' } as any);

        const task = createBaseTask();
        task.plan = {
            steps: [],
            files_to_change: [],
            tests_to_run: ["npm test"],
            expected_behavior: "pass",
            rollback_points: []
        };

        const result = await TestRunnerService.runTests(task);

        expect(result.ok).toBe(true);
        expect(result.artifacts?.command).toBe('npm test');
    });

    it('falls back to default command if requested command is NOT in allowlist', async () => {
        mockPromisifiedExec.mockResolvedValueOnce({ stdout: 'default passed', stderr: '' } as any);

        const task = createBaseTask();
        task.plan = {
            steps: [],
            files_to_change: [],
            tests_to_run: ["rm -rf /"], // Malicious command
            expected_behavior: "fail",
            rollback_points: []
        };

        const consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation(() => { });
        const result = await TestRunnerService.runTests(task);

        expect(result.ok).toBe(true);
        expect(result.artifacts?.command).toBe('npm run lint'); // The fallback
        expect(consoleWarnSpy).toHaveBeenCalledWith(expect.stringContaining("not in allowlist"));

        consoleWarnSpy.mockRestore();
    });

    it('captures failures correctly (non-zero exit code)', async () => {
        const error: any = new Error('Command failed');
        error.code = 1;
        error.stdout = 'some output';
        error.stderr = 'some error';
        mockPromisifiedExec.mockRejectedValueOnce(error);

        const task = createBaseTask();
        const result = await TestRunnerService.runTests(task);

        expect(result.ok).toBe(false);
        expect(result.status).toBe('failed');
        expect(result.artifacts?.exit_code).toBe(1);
        expect(result.artifacts?.stdout).toBe('some output');
        expect(result.artifacts?.stderr).toBe('some error');
        expect(result.error).toBe('Tests failed');
    });

    it('handles execution timeouts specifically', async () => {
        const error: any = new Error('Command timed out');
        error.killed = true;
        error.signal = 'SIGTERM';
        mockPromisifiedExec.mockRejectedValueOnce(error);

        const task = createBaseTask();
        const result = await TestRunnerService.runTests(task);

        expect(result.ok).toBe(false);
        expect(result.status).toBe('failed');
        expect(result.artifacts?.exit_code).toBe(124);
        expect(result.error).toBe('Test execution timed out after 30s');
    });

    it('truncates very long stdout/stderr to 2000 characters', async () => {
        const longOutput = 'a'.repeat(3000);
        const expectedOutput = 'a'.repeat(2000);

        mockPromisifiedExec.mockResolvedValueOnce({ stdout: longOutput, stderr: longOutput } as any);

        const task = createBaseTask();
        const result = await TestRunnerService.runTests(task);

        expect(result.ok).toBe(true);
        expect(result.artifacts?.stdout.length).toBe(2000);
        expect(result.artifacts?.stderr.length).toBe(2000);
        expect(result.artifacts?.stdout).toBe(expectedOutput);
    });
});
