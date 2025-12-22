/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ProjectRole } from './ProjectRole';
export type InvitationCreate = {
    role?: ProjectRole;
    email?: (string | null);
    /**
     * Сколько раз можно использовать ссылку. None = безлимит.
     */
    maxUses?: (number | null);
    /**
     * Срок действия в днях
     */
    expiresInDays?: number;
};

