/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { TaskPriority } from './TaskPriority';
export type TaskUpdate = {
    title?: (string | null);
    description?: (string | null);
    priority?: (TaskPriority | null);
    assigneeId?: (number | null);
    tagIds?: (Array<number> | null);
};

