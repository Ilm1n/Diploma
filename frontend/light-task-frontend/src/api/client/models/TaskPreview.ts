/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { TagRead } from './TagRead';
import type { TaskPriority } from './TaskPriority';
export type TaskPreview = {
    title: string;
    priority?: (TaskPriority | null);
    assigneeId?: (number | null);
    deadlineAt?: (string | null);
    id: number;
    columnId: number;
    projectId: number;
    position: number;
    tags?: Array<TagRead>;
};

