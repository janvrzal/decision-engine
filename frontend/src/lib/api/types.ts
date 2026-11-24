import type { components } from './schema';

/** Zkratky ke generovaným typům API (nepsat ručně, ADR-0007). */
type Schemas = components['schemas'];

export type ViewModel = Schemas['ViewModel'];
export type ProposalView = Schemas['ProposalView'];
export type ResultView = Schemas['ResultView'];
export type MessageView = Schemas['MessageView'];
export type StepView = Schemas['StepView'];
export type StepState = Schemas['StepState'];
export type BarView = Schemas['BarView'];
export type MetricsView = Schemas['MetricsView'];
export type CostView = Schemas['CostView'];
export type ObjectiveOption = Schemas['ObjectiveOption'];
export type Objective = Schemas['Objective'];
export type SolutionStatus = Schemas['SolutionStatus'];
export type IntCell = Schemas['IntCell'];
export type TextCell = Schemas['TextCell'];
export type MoneyCell = Schemas['MoneyCell'];
export type ProposalEdited = Schemas['ProposalEdited'];
export type FieldErrorView = Schemas['FieldErrorView'];

export type UserEvent =
	| Schemas['MessageSent']
	| Schemas['ToolSelected']
	| Schemas['EditRequested']
	| Schemas['ProjectImported']
	| Schemas['ProjectSaved']
	| Schemas['NewProjectRequested']
	| Schemas['ProposalEdited']
	| Schemas['ProposalConfirmed']
	| Schemas['ProposalRejected']
	| Schemas['SolveRequested'];
