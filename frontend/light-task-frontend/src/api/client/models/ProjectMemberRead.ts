/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ProjectRole } from './ProjectRole';
import type { UserPublic } from './UserPublic';
export type ProjectMemberRead = {
    id: number;
    user: UserPublic;
    role: ProjectRole;
    joinedAt: string;
};

