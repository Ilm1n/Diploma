/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ProjectRole } from './ProjectRole';
export type ProjectRead = {
    name: string;
    description?: (string | null);
    color?: string;
    id: number;
    ownerId: number;
    createdAt: string;
    updatedAt: string;
    currentUserRole?: (ProjectRole | null);
};

