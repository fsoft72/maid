<script module lang="ts">
	/*
	This file has been extracted from the Liwe3 project and it used here for testing purposes.
	See https://www.liwe.org for more information.

	(C) Copyright 2024 Fabio Rotondo - OS3 srl
	*/
	import Button from '$liwe3/components/Button.svelte';
	import type { Color, Variant } from '$liwe3/types/types';
	import { filterModes } from '$liwe3/utils/match_filter';

	import type { IconSource } from 'svelte-hero-icons';
	import Checkbox from './Checkbox.svelte';
	import { format_date, toBool } from '$liwe3/utils/utils';
	import Avatar from './Avatar.svelte';
	import Input from './Input.svelte';
	import Paginator from './Paginator.svelte';
	import { onMount } from 'svelte';

	export interface DataGridFieldExtra {
		options?: { label: string; value: string }[];
		dateFormat?: string;
	}

	export interface DataGridField {
		name: string;
		type: string;
		label?: string;
		sortable?: boolean;
		filterable?: boolean;
		searchMode?: filterModes;
		editable?: boolean;
		deletable?: boolean;
		hidden?: boolean;
		align?: string;
		width?: string;
		nowrap?: boolean;
		pre?: string;
		extra?: DataGridFieldExtra;

		render?: (value: any, row: any) => any;

		onclick?: (row: any) => void;
	}

	export interface DataGridRow {
		id: string;
		[key: string]: any;
	}

	export interface DataGridAction {
		id?: string;
		label?: string;
		icon?: IconSource;
		mode?: Color;
		variant?: Variant;

		onclick?: (row: DataGridRow) => void;
		action?: (row: DataGridRow) => void;
	}

	export interface DataGridButton {
		id?: string;
		label?: string;
		icon?: IconSource;
		mode?: Color;
		variant?: Variant;
		onclick: (checked?: boolean) => void;
		type?: 'button' | 'checkbox'; // New property
		checked?: boolean; // New property for checkbox state

		action?: () => void;
	}
</script>

<script lang="ts">
	interface Props {
		fields: DataGridField[];
		data: DataGridRow[];
		actions?: DataGridAction[];
		buttons?: DataGridButton[];

		filters?: Record<string, any>;

		title?: string; // DataGrid title
		mode?: Color;
		viewMode?: string;

		// paginator
		disablePaginator?: boolean;
		rowsPerPage?: number;
		page?: number;
		totalRows?: number;

		// events
		oncelledit?: (row: DataGridRow, field: string, oldValue: any, newValue: any) => void;

		onupdatefield?: (row: DataGridRow, field_name: string, value: any) => void;
		onfilterchange?: (filters: Record<string, any>) => void;

		// paginator event
		onpagechange?: (page: number, rows: number) => void;
	}

	let {
		fields,
		data: _data,
		filters = $bindable({}),
		actions,
		buttons,
		title,
		mode = $bindable('mode3'),
		viewMode = $bindable('comfy'),

		// paginator
		disablePaginator,
		page = $bindable(1),
		totalRows,
		rowsPerPage = $bindable(10),

		// events
		oncelledit,
		onupdatefield,
		onfilterchange,

		// paginator event
		onpagechange
	}: Props = $props();

	let sortField: string | null = $state(null);
	let sortDirection: 'asc' | 'desc' = $state('asc');
	let tableElement: HTMLTableElement | null = $state(null);
	let editingCell: { rowIndex: number; field: string } | null = $state(null);
	let data: DataGridRow[] = $state($state.snapshot(_data));
	let has_filters = fields.some((f) => f.filterable);
	let dataView: HTMLDivElement | null = $state(null);
	let paginator: any = $state(null);

	$effect(() => {
		data = $state.snapshot(_data);
	});

	$effect(() => {
		if (page) dataView?.scrollTo(0, 0);
	});

	let internalFilteredData: DataGridRow[] = $derived.by(() => {
		// if user defined onfilterchange, we don't filter the data
		if (onfilterchange) return data;
		if (!filters || Object.keys(filters).length == 0) return data;

		const res: DataGridRow[] = [];

		data.forEach((row) => {
			let add = true;

			for (const field in filters) {
				const filter = filters[field];

				if (filter.mode == filterModes.contains) {
					if (filter) {
						if (!row[field] || row[field].toLowerCase().indexOf(filter.value.toLowerCase()) == -1) {
							add = false;
						}
					}
				}
			}

			if (add) res.push(row);
		});

		// reset page
		// paginator.resetPage();

		return res;
	});

	let paginatedData: DataGridRow[] = $derived.by(() => {
		if (disablePaginator) return internalFilteredData;

		return internalFilteredData.slice((page - 1) * rowsPerPage, page * rowsPerPage);
	});

	let totRows = $derived.by(() => {
		if (totalRows) return totalRows;

		return internalFilteredData.length;
	});

	function sortData(field: string): void {
		const fieldDef = fields.find((f) => f.name === field);
		if (!fieldDef || !fieldDef.sortable) return; // Only sort if field is sortable

		if (sortField === field) {
			sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
		} else {
			sortField = field;
			sortDirection = 'asc';
		}

		data = data.sort((a, b) => {
			if (a[field] < b[field]) return sortDirection === 'asc' ? -1 : 1;
			if (a[field] > b[field]) return sortDirection === 'asc' ? 1 : -1;
			return 0;
		});
	}

	function startResize(e: MouseEvent, field: string): void {
		e.preventDefault();
		const startX = e.clientX;
		const th = (e.target as HTMLElement).closest('th') as HTMLTableCellElement;
		const startWidth = th.offsetWidth;

		function onMouseMove(e: MouseEvent): void {
			const width = startWidth + e.clientX - startX;
			th.style.width = `${width}px`;
		}

		function onMouseUp(): void {
			document.removeEventListener('mousemove', onMouseMove);
			document.removeEventListener('mouseup', onMouseUp);
		}

		document.addEventListener('mousemove', onMouseMove);
		document.addEventListener('mouseup', onMouseUp);
	}

	function startEditing(rowIndex: number, field: string): void {
		if (fields.find((f) => f.name === field)?.editable) {
			editingCell = { rowIndex, field };
		}
	}

	function finishEditing(row: DataGridRow, field: string, event: Event): void {
		const input = event.target as HTMLInputElement;
		const newValue = input.value;
		const oldValue = row[field];

		if (newValue !== oldValue.toString()) {
			const updatedRow = { ...row, [field]: newValue };
			data[editingCell!.rowIndex] = updatedRow;
			// data = [...data]; // Trigger Svelte reactivity

			if (onupdatefield) {
				console.warn('=== WARN: onupdatefield is deprecated. Use oncelledit instead.');
				onupdatefield(updatedRow, field, newValue);
				return;
			}

			oncelledit?.(updatedRow, field, oldValue, newValue);
		}

		editingCell = null;
	}

	function handleKeyDown(event: KeyboardEvent, row: DataGridRow, field: string): void {
		if (event.key === 'Enter') {
			finishEditing(row, field, event);
		} else if (event.key === 'Escape') {
			editingCell = null;
		}
	}

	function handleButtonClick(button: DataGridButton) {
		if (button.type === 'checkbox') {
			button.checked = !button.checked;
		}
		button.onclick(button.checked);
	}

	const viewModes = ['condensed', 'comfy', 'large'];
	const changeViewMode = (mode: string) => {
		viewMode = mode;
	};

	const _do_filter = (filters: Record<string, any>) => {
		paginator && paginator.resetPage();
		if (onfilterchange) onfilterchange(filters);
	};

	const filter_change = (e: Event) => {
		const input = e.target as HTMLInputElement;
		const name = input.name.replace('f_', '');
		const field = fields.find((f) => f.name === name);
		let value: any = input.value;
		let mode = field?.searchMode || filterModes.contains;

		if (name.endsWith('_1')) {
			mode = filterModes['>='];
		} else if (name.endsWith('_2')) {
			mode = filterModes['<='];
		}

		// we add to the query only checkboxes that are set to true
		if (input.type == 'checkbox' && toBool(value) == false) {
			const nf = { ...filters };
			delete nf[name];

			filters = nf;
			return _do_filter(filters);
		} else if (input.type == 'checkbox' && toBool(value) == true) {
			value = true;
		}

		const new_filters = {
			...filters,
			[name]: {
				mode,
				value
			}
		};

		// remove from new_filters the filters that have an empty value
		for (const key in new_filters) {
			const filter = new_filters[key];
			if (!filter.value) delete new_filters[key];
		}

		filters = new_filters;

		_do_filter(filters);
	};

	const internalPageChange = (page_: number, rows: number) => {
		if (onpagechange) {
			onpagechange(page_, rows);
			return;
		}

		page = page_;
	};

	onMount(() => {
		// console.log('=== DataGrid mounted');
		// get the container height
		if (dataView) {
			const container = dataView.parentElement;
			if (container) {
				const height = container.clientHeight;
				dataView.style.height = `${height - 40}px`;
			}
		}
	});
</script>

{#snippet filtersRow()}
	<!-- filters -->
	{#if has_filters}
		<tr>
			{#each fields as field}
				{#if !field.hidden}
					<td class="filter" style={`width: ${field.width || 'min-content'};`}>
						{#if field.filterable}
							{#if field.type == 'string'}
								<Input
									{mode}
									width={field.width}
									size="xs"
									name={`f_${field.name}`}
									onchange={filter_change}
									value={filters[field.name]?.value}
								/>
							{:else if field.type == 'number'}
								{@const fn1 = `f_${field.name}_1`}
								{@const fn2 = `f_${field.name}_2`}
								<Input
									{mode}
									size="xs"
									type="number"
									name={fn1}
									onchange={filter_change}
									value={filters[fn1]?.value}
								/>
								<Input
									{mode}
									size="xs"
									type="number"
									name={fn2}
									value={filters[fn2]?.value}
									onchange={filter_change}
								/>
							{:else if field.type == 'date'}
								{@const fn1 = `f_${field.name}_1`}
								{@const fn2 = `f_${field.name}_2`}
								<Input
									{mode}
									size="xs"
									type="date"
									name={fn1}
									value={filters[fn1]?.value}
									onchange={filter_change}
								/>
								<Input
									{mode}
									size="xs"
									type="date"
									name={fn2}
									value={filters[fn2]?.value}
									onchange={filter_change}
								/>
							{:else if ['bool', 'boolean', 'checkbox'].indexOf(field.type) != -1}
								<Checkbox
									{mode}
									name={`f_${field.name}`}
									size="xs"
									onchange={filter_change}
									checked={toBool(filters[field.name]?.value)}
								/>
							{/if}
						{/if}
					</td>
				{/if}
			{/each}
			<td></td>
		</tr>
	{/if}
{/snippet}

{#snippet titleBar()}
	{#if title || buttons}
		<div class="title-bar">
			<div class="title">
				{title}
			</div>

			<div class="view-modes">
				{#each viewModes as vm}
					<Button
						mode={vm == viewMode ? 'mode4' : 'mode1'}
						onclick={() => changeViewMode(vm)}
						size="xs"
					>
						{vm}
					</Button>
				{/each}
			</div>

			{#if buttons}
				<div class="buttons">
					{#each buttons as button}
						{#if button.type === 'checkbox'}
							<Checkbox
								size="xs"
								mode={button.mode || mode}
								checked={button.checked || false}
								onchange={() => handleButtonClick(button)}
								label={button.label}
							/>
						{:else}
							<Button
								size="xs"
								mode={button.mode || mode}
								variant={button.variant}
								icon={button.icon}
								onclick={() => handleButtonClick(button)}
							>
								{button.label}
							</Button>
						{/if}
					{/each}
				</div>
			{/if}
		</div>
	{/if}
{/snippet}

{#snippet tableHeaders()}
	<tr>
		{#each fields as field}
			{#if !field.hidden}
				<th onclick={() => sortData(field.name)}>
					{field.label || field.name}
					{#if field.sortable && sortField === field.name}
						{sortDirection === 'asc' ? '▲' : '▼'}
					{/if}
					<!-- svelte-ignore a11y_no_static_element_interactions -->
					<div class="resizer" onmousedown={(e) => startResize(e, field.name)}></div>
				</th>
			{/if}
		{/each}
		{#if actions}
			<th class="actions-header">Actions</th>
		{/if}
	</tr>
{/snippet}

<div class="container">
	<div bind:this={dataView} class="dataview">
		{@render titleBar()}
		<table bind:this={tableElement} class={viewMode}>
			<thead>
				{@render tableHeaders()}
				{@render filtersRow()}
			</thead>
			<tbody>
				{#each paginatedData as row, rowIndex}
					<tr>
						{#each fields as field}
							{#if !field.hidden}
								<td
									ondblclick={() => startEditing(rowIndex, field.name)}
									style:text-align={field.align}
								>
									{#if editingCell && editingCell.rowIndex === rowIndex && editingCell.field === field.name}
										<input
											type="text"
											value={row[field.name]}
											onblur={(e) => finishEditing(row, field.name, e)}
											onkeydown={(e) => handleKeyDown(e, row, field.name)}
										/>
									{:else if field.render}
										{#if field.onclick}
											<Button
												mode="mode4"
												size="sm"
												variant="outline"
												onclick={() => field.onclick && field.onclick(row)}
											>
												{@html field.render(row[field.name], row)}
											</Button>
										{:else}
											{@html field.render(row[field.name], row)}
										{/if}
									{:else if ['bool', 'boolean', 'checkbox'].includes(field.type)}
										<Checkbox
											{mode}
											checked={toBool(row[field.name])}
											onchange={(e: any) => {
												row[field.name] = e.target.checked;
												if (onupdatefield) {
													console.warn(
														'=== WARN: onupdatefield is deprecated. Use oncelledit instead.'
													);
													onupdatefield(row, field.name, e.target.checked);
													return;
												}
												oncelledit?.(row, field.name, !e.target.checked, e.target.checked);
												if (field.onclick) field.onclick(row);
											}}
										/>
									{:else if field.onclick}
										<Button
											mode="mode4"
											size="sm"
											variant="outline"
											onclick={() => field.onclick && field.onclick(row)}
										>
											{row[field.name]}
										</Button>
									{:else if field.type == 'date'}
										{#if field.extra?.dateFormat}
											{format_date(row[field.name], field.extra.dateFormat)}
										{:else}
											{row[field.name]}
										{/if}
									{:else if field.pre}
										<pre>{row[field.name]}</pre>
									{:else if field.type == 'avatar'}
										<Avatar size="64px" value={row} />
									{:else}
										{row[field.name]}
									{/if}
								</td>
							{/if}
						{/each}
						{#if actions}
							<td class="actions-cell">
								<div class="actions">
									{#each actions as action}
										<Button
											size="xs"
											mode={action.mode || mode}
											variant={action.variant}
											icon={action.icon}
											onclick={() => {
												if (action.action) {
													console.warn(
														"WARNING: use of deprecated 'action' property in DataGridAction. Use 'onclick' instead."
													);
													action.action(row);
													return;
												}
												action.onclick && action.onclick(row);
											}}>{action.label ?? ''}</Button
										>
									{/each}
								</div>
							</td>
						{/if}
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
	{#if !disablePaginator}
		<Paginator
			bind:this={paginator}
			total={totRows}
			rows={rowsPerPage}
			onpagechange={internalPageChange}
		/>
	{/if}
</div>

<style>
	:root {
		--table-font-size: 0.8rem;
		--table-font-color: var(--liwe3-color);
		--table-font-family: var(--liwe3-main-font-family);
	}

	.container {
		position: relative;
		width: 100%;
		height: 100%;

		min-height: 250px;

		border: 1px solid var(--liwe3-button-border);
		border-radius: var(--liwe3-border-radius);
	}

	.dataview {
		position: relative;

		width: 100%;
		height: 100%; /* Set a fixed height or use a responsive value */

		overflow: auto;
		scrollbar-width: thin;
		scrollbar-color: var(--liwe3-darker-paper) var(--liwe3-paper);

		background-color: var(--liwe3-paper);
		color: var(--liwe3-color);

		font-size: var(--table-font-size);
		font-family: var(--table-font-family);

		border-radius: var(--liwe3-border-radius);
	}

	.title-bar {
		display: flex;
		flex-direction: row;
		justify-content: space-between;
		align-items: center;
		padding: 4px;

		background-color: var(--liwe3-darker-paper);
	}

	.title {
		font-weight: bold;
	}

	.buttons,
	.actions {
		display: flex;
		flex-direction: row;
		gap: 0.5rem;
	}

	table {
		width: 100%;
		border-collapse: separate;
		border-spacing: 0;

		border-radius: var(--liwe3-border-radius);
		border-collapse: collapse;
	}

	thead {
		position: sticky;
		top: -1px;
		z-index: 1;
		background-color: var(--liwe3-darker-paper);

		border-bottom: 1px solid var(--liwe3-button-border);
	}

	th,
	td {
		text-align: left;
		border: 1px solid var(--liwe3-secondary-color);
	}

	th {
		padding: 8px;
		background-color: var(--liwe3-darker-paper);
	}

	.condensed td {
		padding: 3px;
	}

	.comfy td {
		padding: 8px;
	}

	.large td {
		padding: 24px;
	}

	th {
		cursor: pointer;
		position: relative;
		background-color: var(--liwe3-secondary-color);

		user-select: none;
	}

	tr {
		border-bottom: 1px solid var(--liwe3-tertiary-color);
		max-height: 2rem;
	}

	tr:hover {
		background-color: var(--liwe3-lighter-paper) !important;
	}

	td {
		border-right: 1px solid var(--liwe3-button-border);
	}

	tbody tr:nth-child(even) {
		background-color: var(--liwe3-darker-paper);
	}

	.resizer {
		position: absolute;
		right: 0;
		top: 0;
		height: 100%;
		width: 5px;
		background: rgba(0, 0, 0, 0.3);
		cursor: col-resize;
	}

	.actions-header,
	.actions-cell {
		width: 1%;
		white-space: nowrap;
	}

	input {
		width: 100%;
		box-sizing: border-box;
		padding: 4px;
	}
</style>
