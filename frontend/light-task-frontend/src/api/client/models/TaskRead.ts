/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { TagRead } from './TagRead';
import type { TaskPriority } from './TaskPriority';
export type TaskRead = {
    title: string;
    description?: (string | null);
    priority?: TaskPriority;
    assigneeId?: (number | null);
    id: number;
    columnId: number;
    projectId: number;
    authorId: (number | null);
    position: number;
    createdAt: string;
    updatedAt: string;
    tags?: Array<TagRead>;
};

