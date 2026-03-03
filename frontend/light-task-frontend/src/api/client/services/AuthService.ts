/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Body_login_for_access_token_api_auth_login_post } from '../models/Body_login_for_access_token_api_auth_login_post';
import type { Token } from '../models/Token';
import type { CancelablePromise } from '../core/CancelablePromise';
import type { BaseHttpRequest } from '../core/BaseHttpRequest';
export class AuthService {
    constructor(public readonly httpRequest: BaseHttpRequest) {}
    /**
     * Login For Access Token
     * @param formData
     * @returns Token Successful Response
     * @throws ApiError
     */
    public loginForAccessTokenApiAuthLoginPost(
        formData: Body_login_for_access_token_api_auth_login_post,
    ): CancelablePromise<Token> {
        return this.httpRequest.request({
            method: 'POST',
            url: '/api/auth/login',
            formData: formData,
            mediaType: 'application/x-www-form-urlencoded',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Refresh Jwt
     * @param refreshToken
     * @returns Token Successful Response
     * @throws ApiError
     */
    public refreshJwtApiAuthRefreshPost(
        refreshToken?: (string | null),
    ): CancelablePromise<Token> {
        return this.httpRequest.request({
            method: 'POST',
            url: '/api/auth/refresh',
            cookies: {
                'refresh_token': refreshToken,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Logout
     * @returns any Successful Response
     * @throws ApiError
     */
    public logoutApiAuthLogoutPost(): CancelablePromise<any> {
        return this.httpRequest.request({
            method: 'POST',
            url: '/api/auth/logout',
        });
    }
}
