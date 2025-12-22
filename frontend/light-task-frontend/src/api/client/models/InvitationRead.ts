/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ProjectRole } from './ProjectRole';
export type InvitationRead = {
    id: number;
    token: string;
    role: ProjectRole;
    email: (string | null);
    maxUses: (number | null);
    usedCount: number;
    expiresAt: string;
    link: string;
};

