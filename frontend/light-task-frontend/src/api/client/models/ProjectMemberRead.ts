/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ProjectRole } from './ProjectRole';
import type { UserCollaborator } from './UserCollaborator';
export type ProjectMemberRead = {
    id: number;
    user: UserCollaborator;
    role: ProjectRole;
    joinedAt: string;
};

