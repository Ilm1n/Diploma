/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { TaskRead } from './TaskRead';
export type ColumnRead = {
    name: string;
    tasksLimit: (number | null);
    id: number;
    projectId: number;
    position: number;
    tasks?: Array<TaskRead>;
};

