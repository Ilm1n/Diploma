/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { TaskPriority } from './TaskPriority';
export type TaskCreate = {
    title: string;
    priority?: TaskPriority;
    assigneeId?: (number | null);
    description: (string | null);
    tagIds?: Array<number>;
};

