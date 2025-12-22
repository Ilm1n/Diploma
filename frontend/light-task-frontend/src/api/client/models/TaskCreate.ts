/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { TaskPriority } from './TaskPriority';
export type TaskCreate = {
    title: string;
    description?: (string | null);
    priority?: TaskPriority;
    assigneeId?: (number | null);
    tagIds?: Array<number>;
};

