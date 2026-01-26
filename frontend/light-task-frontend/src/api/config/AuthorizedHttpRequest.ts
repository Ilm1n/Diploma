import type { ApiRequestOptions } from '../client/core/ApiRequestOptions';
import { BaseHttpRequest } from '../client/core/BaseHttpRequest';
import type { OpenAPIConfig } from '../client/core/OpenAPI';
import type { CancelablePromise } from '../client/core/CancelablePromise';
import { request as __request } from '../client/core/request';
import { apiInstance } from './axios-instance';

export class AuthorizedHttpRequest extends BaseHttpRequest {
  constructor(config: OpenAPIConfig) {
    super(config);
  }


  public override request<T>(options: ApiRequestOptions): CancelablePromise<T> {
    return __request(this.config, options, apiInstance as any);
  }
}