/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ApiRequestOptions } from './ApiRequestOptions';
import { BaseHttpRequest } from './BaseHttpRequest';
import type { CancelablePromise } from './CancelablePromise';
import type { OpenAPIConfig } from './OpenAPI';
import { request as __request } from './request';

export class AxiosHttpRequest extends BaseHttpRequest {

    constructor(config: OpenAPIConfig) {
        super(config);
    }


    public override request<T>(options: ApiRequestOptions): CancelablePromise<T> {
        return __request(this.config, options);
    }
}
