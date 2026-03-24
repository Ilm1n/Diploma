/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ProjectCreate } from '../models/ProjectCreate';
import type { ProjectMemberRead } from '../models/ProjectMemberRead';
import type { ProjectMemberUpdate } from '../models/ProjectMemberUpdate';
import type { ProjectRead } from '../models/ProjectRead';
import type { ProjectUpdate } from '../models/ProjectUpdate';
import type { CancelablePromise } from '../core/CancelablePromise';
import type { BaseHttpRequest } from '../core/BaseHttpRequest';
export class ProjectsService {
    constructor(public readonly httpRequest: BaseHttpRequest) {}
    /**
     * Create Project
     * @param requestBody
     * @param xClientMutationId
     * @returns ProjectRead Successful Response
     * @throws ApiError
     */
    public createProjectApiProjectsPost(
        requestBody: ProjectCreate,
        xClientMutationId?: (string | null),
    ): CancelablePromise<ProjectRead> {
        return this.httpRequest.request({
            method: 'POST',
            url: '/api/projects/',
            headers: {
                'X-Client-Mutation-Id': xClientMutationId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get My Projects
     * @returns ProjectRead Successful Response
     * @throws ApiError
     */
    public getMyProjectsApiProjectsGet(): CancelablePromise<Array<ProjectRead>> {
        return this.httpRequest.request({
            method: 'GET',
            url: '/api/projects/',
        });
    }
    /**
     * Get Project Details
     * @param projectId
     * @returns ProjectRead Successful Response
     * @throws ApiError
     */
    public getProjectDetailsApiProjectsProjectIdGet(
        projectId: number,
    ): CancelablePromise<ProjectRead> {
        return this.httpRequest.request({
            method: 'GET',
            url: '/api/projects/{project_id}',
            path: {
                'project_id': projectId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update Project
     * @param projectId
     * @param requestBody
     * @param xClientMutationId
     * @returns ProjectRead Successful Response
     * @throws ApiError
     */
    public updateProjectApiProjectsProjectIdPatch(
        projectId: number,
        requestBody: ProjectUpdate,
        xClientMutationId?: (string | null),
    ): CancelablePromise<ProjectRead> {
        return this.httpRequest.request({
            method: 'PATCH',
            url: '/api/projects/{project_id}',
            path: {
                'project_id': projectId,
            },
            headers: {
                'X-Client-Mutation-Id': xClientMutationId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete Project
     * @param projectId
     * @param xClientMutationId
     * @returns void
     * @throws ApiError
     */
    public deleteProjectApiProjectsProjectIdDelete(
        projectId: number,
        xClientMutationId?: (string | null),
    ): CancelablePromise<void> {
        return this.httpRequest.request({
            method: 'DELETE',
            url: '/api/projects/{project_id}',
            path: {
                'project_id': projectId,
            },
            headers: {
                'X-Client-Mutation-Id': xClientMutationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Project Members
     * @param projectId
     * @returns ProjectMemberRead Successful Response
     * @throws ApiError
     */
    public getProjectMembersApiProjectsProjectIdMembersGet(
        projectId: number,
    ): CancelablePromise<Array<ProjectMemberRead>> {
        return this.httpRequest.request({
            method: 'GET',
            url: '/api/projects/{project_id}/members',
            path: {
                'project_id': projectId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Remove Project Member
     * @param projectId
     * @param userId
     * @param xClientMutationId
     * @returns void
     * @throws ApiError
     */
    public removeProjectMemberApiProjectsProjectIdMembersUserIdDelete(
        projectId: number,
        userId: number,
        xClientMutationId?: (string | null),
    ): CancelablePromise<void> {
        return this.httpRequest.request({
            method: 'DELETE',
            url: '/api/projects/{project_id}/members/{user_id}',
            path: {
                'project_id': projectId,
                'user_id': userId,
            },
            headers: {
                'X-Client-Mutation-Id': xClientMutationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update Member Role
     * @param projectId
     * @param userId
     * @param requestBody
     * @param xClientMutationId
     * @returns ProjectMemberRead Successful Response
     * @throws ApiError
     */
    public updateMemberRoleApiProjectsProjectIdMembersUserIdPatch(
        projectId: number,
        userId: number,
        requestBody: ProjectMemberUpdate,
        xClientMutationId?: (string | null),
    ): CancelablePromise<ProjectMemberRead> {
        return this.httpRequest.request({
            method: 'PATCH',
            url: '/api/projects/{project_id}/members/{user_id}',
            path: {
                'project_id': projectId,
                'user_id': userId,
            },
            headers: {
                'X-Client-Mutation-Id': xClientMutationId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
