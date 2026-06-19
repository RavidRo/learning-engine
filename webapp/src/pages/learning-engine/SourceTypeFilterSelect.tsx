import { type ChangeEvent } from "react";

import { type SourceTypeFilter, sourceTypeFilterOptions } from "./sourceTypeFilters";

type SourceTypeFilterSelectProps = {
  label: string;
  onChange: (sourceTypeFilter: SourceTypeFilter) => void;
  value: SourceTypeFilter;
};

export const SourceTypeFilterSelect = ({ label, onChange, value }: SourceTypeFilterSelectProps) => {
  const handleChange = (event: ChangeEvent<HTMLSelectElement>): void => {
    onChange(event.target.value as SourceTypeFilter);
  };

  return (
    <label className="source-type-filter-control">
      <span>{label}</span>
      <select value={value} onChange={handleChange} aria-label={label}>
        {sourceTypeFilterOptions.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
};
