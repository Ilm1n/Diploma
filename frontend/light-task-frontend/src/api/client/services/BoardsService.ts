/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ColumnCreate } from '../models/ColumnCreate';
import type { ColumnRead } from '../models/ColumnRead';
import type { ColumnReorderRequest } from '../models/ColumnReorderRequest';
import type { ColumnUpdate } from '../models/ColumnUpdate';
import type { TaskCreate } from '../models/TaskCreate';
import type { TaskMove } from '../models/TaskMove';
import type { TaskMoveResponse } from '../models/TaskMoveResponse';
import type { TaskPreview } from '../models/TaskPreview';
import type { TaskRead } from '../models/TaskRead';
import type { TaskUpdate } from '../models/TaskUpdate';
import type { CancelablePromise } from '../core/CancelablePromise';
import type { BaseHttpRequest } from '../core/BaseHttpRequest';
export class BoardsService {
    constructor(public readonly httpRequest: BaseHttpRequest) {}
    /**
     * Get Project Board
     * @param projectId
     * @returns ColumnRead Successful Response
     * @throws ApiError
     */
    public getProjectBoardApiProjectsProjectIdColumnsGet(
        projectId: number,
    ): CancelablePromise<Array<ColumnRead>> {
        return this.httpRequest.request({
            method: 'GET',
            url: '/api/projects/{project_id}/columns',
            path: {
                'project_id': projectId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create Column
     * @param projectId
     * @param requestBody
     * @returns ColumnRead Successful Response
     * @throws ApiError
     */
    public createColumnApiProjectsProjectIdColumnsPost(
        projectId: number,
        requestBody: ColumnCreate,
    ): CancelablePromise<ColumnRead> {
        return this.httpRequest.request({
            method: 'POST',
            url: '/api/projects/{project_id}/columns',
            path: {
                'project_id': projectId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update Column
     * @param projectId
     * @param columnId
     * @param requestBody
     * @returns ColumnRead Successful Response
     * @throws ApiError
     */
    public updateColumnApiProjectsProjectIdColumnsColumnIdPatch(
        projectId: number,
        columnId: number,
        requestBody: ColumnUpdate,
    ): CancelablePromise<ColumnRead> {
        return this.httpRequest.request({
            method: 'PATCH',
            url: '/api/projects/{project_id}/columns/{column_id}',
            path: {
                'project_id': projectId,
                'column_id': columnId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete Column
     * @param projectId
     * @param columnId
     * @returns void
     * @throws ApiError
     */
    public deleteColumnApiProjectsProjectIdColumnsColumnIdDelete(
        projectId: number,
        columnId: number,
    ): CancelablePromise<void> {
        return this.httpRequest.request({
            method: 'DELETE',
            url: '/api/projects/{project_id}/columns/{column_id}',
            path: {
                'project_id': projectId,
                'column_id': columnId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Reorder Columns
     * @param projectId
     * @param requestBody
     * @returns void
     * @throws ApiError
     */
    public reorderColumnsApiProjectsProjectIdColumnsReorderPost(
        projectId: number,
        requestBody: ColumnReorderRequest,
    ): CancelablePromise<void> {
        return this.httpRequest.request({
            method: 'POST',
            url: '/api/projects/{project_id}/columns/reorder',
            path: {
                'project_id': projectId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create Task
     * @param projectId
     * @param columnId
     * @param requestBody
     * @returns TaskRead Successful Response
     * @throws ApiError
     */
    public createTaskApiProjectsProjectIdColumnsColumnIdTasksPost(
        projectId: number,
        columnId: number,
        requestBody: TaskCreate,
    ): CancelablePromise<TaskRead> {
        return this.httpRequest.request({
            method: 'POST',
            url: '/api/projects/{project_id}/columns/{column_id}/tasks',
            path: {
                'project_id': projectId,
                'column_id': columnId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Project Tasks
     * @param projectId
     * @param assigneeId
     * @param tagIds
     * @param search
     * @returns TaskPreview Successful Response
     * @throws ApiError
     */
    public getProjectTasksApiProjectsProjectIdTasksGet(
        projectId: number,
        assigneeId?: (number | null),
        tagIds?: (Array<number> | null),
        search?: (string | null),
    ): CancelablePromise<Array<TaskPreview>> {
        return this.httpRequest.request({
            method: 'GET',
            url: '/api/projects/{project_id}/tasks',
            path: {
                'project_id': projectId,
            },
            query: {
                'assignee_id': assigneeId,
                'tag_ids': tagIds,
                'search': search,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Task Details
     * @param taskId
     * @returns TaskRead Successful Response
     * @throws ApiError
     */
    public getTaskDetailsApiTasksTaskIdGet(
        taskId: number,
    ): CancelablePromise<TaskRead> {
        return this.httpRequest.request({
            method: 'GET',
            url: '/api/tasks/{task_id}',
            path: {
                'task_id': taskId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update Task
     * @param taskId
     * @param requestBody
     * @returns TaskRead Successful Response
     * @throws ApiError
     */
    public updateTaskApiTasksTaskIdPatch(
        taskId: number,
        requestBody: TaskUpdate,
    ): CancelablePromise<TaskRead> {
        return this.httpRequest.request({
            method: 'PATCH',
            url: '/api/tasks/{task_id}',
            path: {
                'task_id': taskId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete Task
     * @param taskId
     * @returns void
     * @throws ApiError
     */
    public deleteTaskApiTasksTaskIdDelete(
        taskId: number,
    ): CancelablePromise<void> {
        return this.httpRequest.request({
            method: 'DELETE',
            url: '/api/tasks/{task_id}',
            path: {
                'task_id': taskId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Move Task
     * @param taskId
     * @param requestBody
     * @returns TaskMoveResponse Successful Response
     * @throws ApiError
     */
    public moveTaskApiTasksTaskIdMovePatch(
        taskId: number,
        requestBody: TaskMove,
    ): CancelablePromise<TaskMoveResponse> {
        return this.httpRequest.request({
            method: 'PATCH',
            url: '/api/tasks/{task_id}/move',
            path: {
                'task_id': taskId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
