/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { TagCreate } from '../models/TagCreate';
import type { TagRead } from '../models/TagRead';
import type { TagUpdate } from '../models/TagUpdate';
import type { CancelablePromise } from '../core/CancelablePromise';
import type { BaseHttpRequest } from '../core/BaseHttpRequest';
export class TagsService {
    constructor(public readonly httpRequest: BaseHttpRequest) {}
    /**
     * Get Project Tags
     * @param projectId
     * @returns TagRead Successful Response
     * @throws ApiError
     */
    public getProjectTagsApiProjectsProjectIdTagsGet(
        projectId: number,
    ): CancelablePromise<Array<TagRead>> {
        return this.httpRequest.request({
            method: 'GET',
            url: '/api/projects/{project_id}/tags',
            path: {
                'project_id': projectId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create Tag
     * @param projectId
     * @param requestBody
     * @returns TagRead Successful Response
     * @throws ApiError
     */
    public createTagApiProjectsProjectIdTagsPost(
        projectId: number,
        requestBody: TagCreate,
    ): CancelablePromise<TagRead> {
        return this.httpRequest.request({
            method: 'POST',
            url: '/api/projects/{project_id}/tags',
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
     * Update Tag
     * @param tagId
     * @param requestBody
     * @returns TagRead Successful Response
     * @throws ApiError
     */
    public updateTagApiTagsTagIdPatch(
        tagId: number,
        requestBody: TagUpdate,
    ): CancelablePromise<TagRead> {
        return this.httpRequest.request({
            method: 'PATCH',
            url: '/api/tags/{tag_id}',
            path: {
                'tag_id': tagId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete Tag
     * @param tagId
     * @returns void
     * @throws ApiError
     */
    public deleteTagApiTagsTagIdDelete(
        tagId: number,
    ): CancelablePromise<void> {
        return this.httpRequest.request({
            method: 'DELETE',
            url: '/api/tags/{tag_id}',
            path: {
                'tag_id': tagId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
