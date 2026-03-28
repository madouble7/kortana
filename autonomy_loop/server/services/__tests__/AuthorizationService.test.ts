import { afterEach, beforeEach, describe, expect, it, jest } from '@jest/globals';
import { AuthorizationService } from '../AuthorizationService.ts';

describe('AuthorizationService', () => {
    beforeEach(() => {
        // Initialize with an in-memory database for testing
        AuthorizationService.init(':memory:');
        jest.spyOn(console, 'log').mockImplementation(() => { });
    });

    afterEach(() => {
        AuthorizationService.close();
        jest.restoreAllMocks();
    });

    it('initially reports a state of unauthorized', () => {
        expect(AuthorizationService.isTaskAuthorized('task-1')).toBe(false);
    });

    it('authorizes a task successfully', () => {
        AuthorizationService.authorizeTask('task-1');
        expect(AuthorizationService.isTaskAuthorized('task-1')).toBe(true);
    });

    it('revokes an authorized task', () => {
        AuthorizationService.authorizeTask('task-1');
        expect(AuthorizationService.isTaskAuthorized('task-1')).toBe(true);

        AuthorizationService.revokeTask('task-1');
        expect(AuthorizationService.isTaskAuthorized('task-1')).toBe(false);
    });

    it('consumes an authorized task', () => {
        AuthorizationService.authorizeTask('task-1');
        expect(AuthorizationService.isTaskAuthorized('task-1')).toBe(true);

        AuthorizationService.consumeTask('task-1');
        expect(AuthorizationService.isTaskAuthorized('task-1')).toBe(false);
    });

    it('respects expiration time', () => {
        // Authorize with a very short expiration (-1 ms so it expires immediately)
        AuthorizationService.authorizeTask('task-1', 'system', 'test', -1);
        expect(AuthorizationService.isTaskAuthorized('task-1')).toBe(false);
    });
});
