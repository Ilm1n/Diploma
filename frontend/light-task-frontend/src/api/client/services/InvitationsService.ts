/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { InvitationAcceptResponse } from '../models/InvitationAcceptResponse';
import type { InvitationCreate } from '../models/InvitationCreate';
import type { InvitationRead } from '../models/InvitationRead';
import type { CancelablePromise } from '../core/CancelablePromise';
import type { BaseHttpRequest } from '../core/BaseHttpRequest';
export class InvitationsService {
    constructor(public readonly httpRequest: BaseHttpRequest) {}
    /**
     * Create Invitation
     * @param projectId
     * @param requestBody
     * @returns InvitationRead Successful Response
     * @throws ApiError
     */
    public createInvitationApiProjectsProjectIdInvitePost(
        projectId: number,
        requestBody: InvitationCreate,
    ): CancelablePromise<InvitationRead> {
        return this.httpRequest.request({
            method: 'POST',
            url: '/api/projects/{project_id}/invite',
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
     * Get Project Invitations
     * @param projectId
     * @returns InvitationRead Successful Response
     * @throws ApiError
     */
    public getProjectInvitationsApiProjectsProjectIdInvitationsGet(
        projectId: number,
    ): CancelablePromise<Array<InvitationRead>> {
        return this.httpRequest.request({
            method: 'GET',
            url: '/api/projects/{project_id}/invitations',
            path: {
                'project_id': projectId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete Invitation
     * @param projectId
     * @param invitationId
     * @returns void
     * @throws ApiError
     */
    public deleteInvitationApiProjectsProjectIdInvitationsInvitationIdDelete(
        projectId: number,
        invitationId: number,
    ): CancelablePromise<void> {
        return this.httpRequest.request({
            method: 'DELETE',
            url: '/api/projects/{project_id}/invitations/{invitation_id}',
            path: {
                'project_id': projectId,
                'invitation_id': invitationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Accept Invitation
     * @param token
     * @returns InvitationAcceptResponse Successful Response
     * @throws ApiError
     */
    public acceptInvitationApiInvitationsTokenAcceptPost(
        token: string,
    ): CancelablePromise<InvitationAcceptResponse> {
        return this.httpRequest.request({
            method: 'POST',
            url: '/api/invitations/{token}/accept',
            path: {
                'token': token,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
